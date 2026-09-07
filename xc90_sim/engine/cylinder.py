"""
One cylinder's real (single-zone-simplified) thermodynamic cycle: piston
position from slider-crank geometry, gas pressure through intake/
compression/combustion/expansion/exhaust via the standard first-law
single-zone combustion ODE with a Wiebe heat-release function --

    dP = [(gamma-1)*dQ_in - gamma*P*dV] / V

the same equation real simplified (non-CFD) engine simulation tools use
(derived from the ideal gas law + first law of thermodynamics for a
closed, no-mass-flow system; see e.g. Heywood's "Internal Combustion
Engine Fundamentals"). Genuine physics, single-zone-level detail (no
flame-front tracking, no multi-zone temperature stratification).

Indicated torque contribution is computed via the energy method
(torque = gauge_pressure * dV/dtheta) rather than the full slider-crank
force-transmission formula -- equivalent for net work/torque, simpler to
get right.
"""

import math

from ..specs import cylinder as specs
from .camshaft import Camshaft
from ..fuel_system import FuelInjector

_BORE_AREA_M2 = math.pi / 4.0 * specs.BORE_M ** 2


def _wiebe_burned_fraction(theta_since_spark_deg):
    if theta_since_spark_deg <= 0.0:
        return 0.0
    if theta_since_spark_deg >= specs.COMBUSTION_DURATION_DEG:
        return 1.0
    frac = theta_since_spark_deg / specs.COMBUSTION_DURATION_DEG
    return 1.0 - math.exp(-specs.WIEBE_EFFICIENCY_FACTOR * frac ** (specs.WIEBE_SHAPE_M + 1.0))


_SPARK_DEG = 360.0 - specs.SPARK_ADVANCE_DEG_BTDC
_COMBUSTION_END_DEG = _SPARK_DEG + specs.COMBUSTION_DURATION_DEG


class Cylinder:
    def __init__(self, phase_offset_deg):
        """phase_offset_deg: this cylinder's offset within the shared 720-degree
        cycle clock the engine advances (0/180/360/540 for 4 evenly-spaced
        cylinders -- see specs.cylinder.FIRING_ORDER's docstring for why the
        real firing-order labeling doesn't matter to this model's physics)."""
        self.phase_offset_deg = phase_offset_deg
        self.pressure_pa = specs.ATMOSPHERIC_PRESSURE_PA
        self.trapped_air_mass_kg = 0.0
        self.fuel_mass_kg = 0.0
        self._fuel_energy_j = 0.0
        self.camshaft = Camshaft()
        self.fuel_injector = FuelInjector()
        # None (not "exhaust"): a cylinder whose phase offset happens to
        # start it mid-compression/combustion/expansion must NOT trigger a
        # spurious "just crossed IVC" charge-trap using the wrong volume on
        # its very first step -- only a real intake-regime visit should ever
        # set this to something that can trigger a trap.
        self._last_regime = None

    def cylinder_angle_deg(self, cycle_angle_deg):
        """This cylinder's own 0-720 position within the shared cycle clock."""
        return (cycle_angle_deg - self.phase_offset_deg) % 720.0

    def volume_m3(self, cylinder_angle_deg):
        """Slider-crank piston position -> instantaneous cylinder volume."""
        theta = math.radians(cylinder_angle_deg % 360.0)
        r = specs.CRANK_RADIUS_M
        rod = specs.CONNECTING_ROD_LENGTH_M
        x = r * (1.0 - math.cos(theta)) + (r ** 2 / (2.0 * rod)) * math.sin(theta) ** 2
        return specs.CLEARANCE_VOLUME_M3 + _BORE_AREA_M2 * x

    def _regime(self, cylinder_angle_deg):
        if self.camshaft.intake_open(cylinder_angle_deg):
            return "intake"
        if self.camshaft.exhaust_open(cylinder_angle_deg):
            return "exhaust"
        if cylinder_angle_deg < _SPARK_DEG:
            return "compression"
        if cylinder_angle_deg < _COMBUSTION_END_DEG:
            return "combustion"
        return "expansion"

    def step(self, cycle_angle_deg, dtheta_deg, effective_map_pa, ve_frac, afr_target, condition,
              fuel_pressure_frac=1.0, backpressure_pa=0.0, dilution_frac=0.0,
              fuel_lhv_j_per_kg=specs.FUEL_LHV_J_PER_KG, combustion_efficiency=specs.COMBUSTION_EFFICIENCY):
        """
        Advances this cylinder by dtheta_deg of crank rotation. Returns this
        cylinder's indicated torque contribution (Nm) for this sub-step.

        effective_map_pa: current effective intake manifold pressure (throttle
        + boost, computed by the engine). ve_frac: volumetric efficiency at
        the current rpm (already includes any EGR dilution derating — see
        Engine._cylinder_torque_sum_nm). afr_target: target air-fuel ratio
        (richens under boost). condition (0..1, 1.0=new): overall engine
        wear -- scales trapped charge, standing in for compression loss/
        carbon buildup. fuel_pressure_frac (0..1): actual/target fuel rail
        pressure, from the FuelPump -- low pressure derates achievable
        injector flow (see FuelInjector). backpressure_pa: real exhaust
        system restriction (catalytic converter + muffler — see
        ExhaustSystem) the exhaust stroke has to push against, a genuine
        (if small) pumping loss. dilution_frac (0..1): combined EGR + PCV
        recirculated-gas fraction of the trapped charge — beyond the
        fresh-charge-displacement effect already folded into ve_frac,
        this also lowers the compression-phase gamma (recirculated
        exhaust gas has a lower specific-heat ratio than fresh air — see
        specs.DILUTED_CHARGE_GAMMA_MIN), a second, smaller real mechanism.
        fuel_lhv_j_per_kg/combustion_efficiency: real fuel-chemistry/aging
        effects — ethanol content lowers effective LHV, stale fuel lowers
        combustion_efficiency (see FuelTank) — default to this project's
        original pure-fresh-gasoline constants so callers that don't pass
        them (e.g. Engine.wide_open_torque_nm's calibration sweep) are
        unaffected.
        """
        own_angle = self.cylinder_angle_deg(cycle_angle_deg)
        new_own_angle = (own_angle + dtheta_deg) % 720.0
        regime = self._regime(new_own_angle)

        v_before = self.volume_m3(own_angle)
        v_after = self.volume_m3(new_own_angle)
        dv = v_after - v_before
        fuel_trapped_kg = 0.0

        if regime in ("intake", "exhaust"):
            self.pressure_pa = (
                effective_map_pa if regime == "intake" else specs.ATMOSPHERIC_PRESSURE_PA + backpressure_pa
            )
            gauge_pa = self.pressure_pa - specs.ATMOSPHERIC_PRESSURE_PA
        else:
            if self._last_regime is not None and self._last_regime in ("intake", "exhaust"):
                # Just crossed IVC: trap the charge for this cycle.
                gas_temp_k = specs.INTAKE_CHARGE_TEMP_K
                self.trapped_air_mass_kg = (
                    condition * ve_frac * effective_map_pa * v_before
                    / (specs.SPECIFIC_GAS_CONSTANT_J_PER_KGK * gas_temp_k)
                )
                commanded_fuel_kg = self.trapped_air_mass_kg / afr_target
                self.fuel_mass_kg = self.fuel_injector.inject(commanded_fuel_kg, fuel_pressure_frac)
                fuel_trapped_kg = self.fuel_mass_kg
                self._fuel_energy_j = self.fuel_mass_kg * fuel_lhv_j_per_kg * combustion_efficiency
                self.pressure_pa = effective_map_pa

            diluted_intake_gamma = specs.INTAKE_GAMMA - dilution_frac * (specs.INTAKE_GAMMA - specs.DILUTED_CHARGE_GAMMA_MIN)
            gamma = diluted_intake_gamma if regime == "compression" else specs.COMBUSTION_GAMMA
            dq_in = 0.0
            if regime == "combustion":
                theta1 = max(0.0, own_angle - _SPARK_DEG)
                theta2 = max(0.0, new_own_angle - _SPARK_DEG)
                dq_in = self._fuel_energy_j * max(0.0, _wiebe_burned_fraction(theta2) - _wiebe_burned_fraction(theta1))

            p_prev = self.pressure_pa
            v_prev = max(v_before, 1e-9)
            dp = ((gamma - 1.0) * dq_in - gamma * p_prev * dv) / v_prev
            self.pressure_pa = p_prev + dp
            gauge_pa = p_prev - specs.ATMOSPHERIC_PRESSURE_PA

        self._last_regime = regime

        torque_nm = 0.0 if dtheta_deg == 0.0 else gauge_pa * dv / math.radians(dtheta_deg)
        return torque_nm, fuel_trapped_kg
