"""
Drive-E 2.0L twincharged I4 engine model: a genuine cylinder-level
combustion model (4 real Cylinder instances + a Camshaft-timed intake/
exhaust cycle -- see cylinder.py/camshaft.py) underneath the exact same
public interface this project's driveline (torque converter, transmission,
Simulation.step()) already depends on. Nothing downstream of Engine had to
change for this -- rpm/omega/throttle/step_locked/step_unlocked/step_off/
step_cranking all mean exactly what they meant before; what changed is
that the torque numbers they produce now come from real per-cylinder
thermodynamics instead of an empirical torque-curve lookup.

Twincharger boost model: supercharger boost is instant and rpm-proportional
(it's belt-driven, mechanically coupled to the crank, no lag); turbo boost
lags toward its target via BOOST_LAG_TAU_S (the real physical reason boost
lag exists at all -- exhaust-energy-driven turbine spin-up). The handoff
between them (supercharger active low-rpm, turbo takes over higher up) is
real, researched behavior -- see specs/cylinder.py's citation.
"""

import numpy as np

from ..specs import engine as specs
from ..specs import cylinder as cyl_specs
from ..specs import accessories as acc_specs
from .cylinder import Cylinder
from .flywheel import Flywheel
from .timing_belt import TimingBelt
from .pcv_valve import PCVValve
from ..electrical import AccessoryBelt, Alternator
from ..fuel_system import FuelPump
from ..electrical import Relay
from ..exhaust import Turbocharger, ExhaustSystem, OxygenSensor, EGRValve
from ..specs import exhaust as exh_specs


def _friction_torque_nm(rpm):
    # ASSUMPTION: simple FMEP-style quadratic fit, ~15 Nm at idle to ~55 Nm at redline.
    # Kept as a separate empirical term even in this cylinder-level model --
    # real detailed engine simulations (e.g. Chen-Flynn friction
    # correlations) also fit mechanical friction/pumping losses empirically
    # rather than deriving them from first principles; this isn't a
    # shortcut specific to this project.
    k = rpm / 1000.0
    return 10.0 + 3.0 * k + 0.6 * k * k


def _supercharger_boost_pa(rpm):
    frac = np.clip(rpm / cyl_specs.SUPERCHARGER_FULL_BOOST_RPM, 0.0, 1.0)
    return cyl_specs.SUPERCHARGER_MAX_BOOST_PA * frac


def _volumetric_efficiency(rpm):
    return float(np.interp(rpm, cyl_specs.VE_RPM_POINTS, cyl_specs.VE_FRACTION_POINTS))


def _target_afr(boost_pa, stoich_afr):
    """stoich_afr: the actual fuel's stoichiometric AFR (see FuelTank.
    effective_stoich_afr() -- ethanol needs much less air per unit fuel
    mass than gasoline). The real ECU enrichment target under boost is
    naturally expressed as a fraction of stoichiometric (lambda), not a
    fixed absolute AFR number, so that relationship (not the absolute
    gasoline-only numbers) is what's preserved here across fuel blends."""
    boost_frac = np.clip(boost_pa / cyl_specs.TURBO_MAX_BOOST_PA, 0.0, 1.0)
    full_boost_lambda = cyl_specs.AFR_AT_FULL_BOOST / cyl_specs.STOICHIOMETRIC_AFR
    afr_at_full_boost = stoich_afr * full_boost_lambda
    return stoich_afr + boost_frac * (afr_at_full_boost - stoich_afr)


def _substep_count(omega, dt):
    """How many combustion sub-steps this outer tick needs to keep
    degrees-per-substep at or below MAX_CRANK_DEG_PER_SUBSTEP -- adaptive,
    not fixed, since a fixed count fine enough at a small outer dt is far
    too coarse at a larger one (see specs.cylinder's docstring)."""
    total_deg = abs(np.degrees(omega * dt))
    n = int(np.ceil(total_deg / cyl_specs.MAX_CRANK_DEG_PER_SUBSTEP))
    return int(np.clip(n, 1, cyl_specs.MAX_CRANK_SUBSTEPS_PER_TICK))


class Engine:
    """Crankshaft rotational dynamics driven by throttle input and driveline load."""

    def __init__(self, condition=1.0, timing_belt_condition=1.0, accessory_belt_condition=1.0):
        """condition (0..1, default 1.0 = like new): overall power-output
        scale for general engine wear (compression loss, carbon buildup at
        high mileage) — see xc90_sim.wear. Scales trapped charge mass
        directly in the combustion model now, rather than scaling an
        empirical torque curve. timing_belt_condition/accessory_belt_condition:
        see WearModel.condition("timing_belt"/"accessory_belt") — both have a
        floor_condition of 1.0 (see wear/wear_model.py), so these never
        actually change engine output; they exist so worn-belt effects
        (TimingBelt's small camshaft retard, AccessoryBelt's alternator
        efficiency loss) are genuinely wired up if that ever changes."""
        self.rpm = specs.IDLE_RPM
        self.throttle = 0.0  # driver pedal position, 0..1
        self.traction_control_limit_frac = 1.0  # set by TractionControl; 1.0 = no cut
        self.condition = condition

        self.cycle_angle_deg = 0.0  # shared 720-degree 4-stroke cycle clock
        self.cylinders = [Cylinder(phase_offset_deg=180.0 * i) for i in range(cyl_specs.CYLINDER_COUNT)]
        self.manifold_pressure_pa = cyl_specs.ATMOSPHERIC_PRESSURE_PA * cyl_specs.IDLE_MAP_FRACTION
        self.total_fuel_burned_kg = 0.0  # monotonic counter -- Simulation reads the delta each tick

        # Real named hardware: a flywheel with its own derived inertia (not
        # a bare constant), a timing belt genuinely enforcing the 2:1 cam:
        # crank ratio (see camshaft_angle_deg), an accessory belt + real
        # alternator whose electrical load comes from whatever's actually
        # switched on (see set_electrical_demand_w), an AC compressor
        # clutch (mechanical, belt-driven — separate from the alternator's
        # electrical load), a real fuel pump with its own pressure state
        # that gates injector flow, a turbocharger owning its own boost
        # lag (the supercharger side has no state -- it's instant, belt-
        # driven -- see _supercharger_boost_pa), an exhaust system (real
        # catalytic converter light-off + backpressure feeding back into
        # the cylinders' exhaust-stroke pumping loss), an O2 sensor per
        # cylinder reading the real AFR being run, and an EGR valve.
        self.flywheel = Flywheel()
        self.timing_belt = TimingBelt(condition=timing_belt_condition)
        self.accessory_belt = AccessoryBelt(condition=accessory_belt_condition)
        self.alternator = Alternator()
        self.fuel_pump = FuelPump()
        # Real relay gating the fuel pump's power feed -- see
        # xc90_sim.electrical.Relay. Invisible under normal operation
        # (contacts follow energized exactly), but a stuck-open fault means
        # the engine cranks and never catches, the real symptom of a dead
        # fuel pump relay.
        self.fuel_pump_relay = Relay()
        self.turbocharger = Turbocharger()
        self.exhaust_system = ExhaustSystem()
        self.oxygen_sensors = [OxygenSensor() for _ in range(cyl_specs.CYLINDER_COUNT)]
        self.egr_valve = EGRValve()
        self.pcv_valve = PCVValve(condition=condition)
        self.electrical_demand_w = 0.0  # set each tick by Simulation from real lighting/HVAC/etc. state
        self.ac_compressor_active = False

        # Real fuel chemistry/aging (see xc90_sim.fuel_system.FuelTank) --
        # defaults match this project's previous hardcoded pure-fresh-
        # gasoline behavior exactly, so nothing changes until Simulation
        # actually starts feeding real tank state in via set_fuel_quality().
        self._fuel_lhv_j_per_kg = cyl_specs.FUEL_LHV_J_PER_KG
        self._fuel_stoich_afr = cyl_specs.STOICHIOMETRIC_AFR
        self._fuel_boost_derate_frac = 0.0
        self._fuel_combustion_efficiency = cyl_specs.COMBUSTION_EFFICIENCY

    def set_fuel_quality(self, lhv_j_per_kg, stoich_afr, boost_derate_frac, combustion_efficiency):
        """Real, connected effect of what's actually in the tank (ethanol
        content, octane shortfall, staleness) — see FuelTank. Called each
        tick by Simulation."""
        self._fuel_lhv_j_per_kg = lhv_j_per_kg
        self._fuel_stoich_afr = stoich_afr
        self._fuel_boost_derate_frac = boost_derate_frac
        self._fuel_combustion_efficiency = combustion_efficiency

    @property
    def total_rotating_inertia_kgm2(self):
        return self.flywheel.inertia_kgm2 + specs.OTHER_ROTATING_INERTIA_KGM2

    @property
    def camshaft_angle_deg(self):
        """The real camshaft's own position (0-360), via the timing belt's
        2:1 ratio (+ a small wear-retard if the belt is worn): cycle_angle_deg
        already spans 0-720 across exactly 2 crank revolutions (one full
        4-stroke cycle), which is precisely the "crank angle" input the
        belt's ratio expects to produce one real camshaft revolution —
        genuinely derived, not a duplicate of the Cylinder-facing clock."""
        return self.timing_belt.camshaft_angle_deg(self.cycle_angle_deg)

    def set_electrical_demand_w(self, watts):
        """Real electrical load from whatever's actually switched on right now
        (headlights, HVAC blower, seat heaters, infotainment, wipers, ...) —
        see Simulation.step() for where this is actually computed."""
        self.electrical_demand_w = max(0.0, watts)

    def set_ac_compressor_active(self, active):
        self.ac_compressor_active = active

    def _accessory_load_torque_nm(self, rpm):
        """Real crank torque draw from accessories: the alternator's load
        (from actual electrical demand, including the fuel pump's own
        draw) plus the AC compressor's mechanical draw when its clutch is
        engaged — replaces what used to be one flat constant."""
        omega = rpm * 2.0 * np.pi / 60.0
        total_electrical_w = (
            self.electrical_demand_w + acc_specs.ALTERNATOR_BASELINE_LOAD_W + self.fuel_pump.electrical_load_w()
        )
        alternator_nm = self.alternator.load_torque_nm(omega, total_electrical_w, self.accessory_belt.condition)
        ac_nm = 0.0
        if self.ac_compressor_active:
            ac_nm = acc_specs.AC_COMPRESSOR_LOAD_NM_AT_1000_RPM * 1000.0 / max(rpm, 100.0)
        return alternator_nm + ac_nm

    @property
    def omega(self):
        """Crankshaft angular velocity, rad/s."""
        return self.rpm * 2.0 * np.pi / 60.0

    @property
    def calculated_load_frac(self):
        """Effective manifold-pressure-based load, 0..1 (0 = idle vacuum, 1 =
        full atmospheric+boost) — analogous to a real ECU's "calculated
        load" PID (0x04), now genuinely derived from manifold pressure
        rather than a throttle-lag proxy."""
        idle_pa = cyl_specs.ATMOSPHERIC_PRESSURE_PA * cyl_specs.IDLE_MAP_FRACTION
        max_pa = cyl_specs.ATMOSPHERIC_PRESSURE_PA + cyl_specs.TURBO_MAX_BOOST_PA
        return float(np.clip((self.manifold_pressure_pa - idle_pa) / (max_pa - idle_pa), 0.0, 1.0))

    def wide_open_torque_nm(self, rpm):
        """Diagnostic/calibration helper: full-throttle, fully-spooled indicated
        torque (Nm) at the given rpm, averaged over one full 720-degree cycle.
        Runs a throwaway set of cylinders so it never disturbs the engine's
        actual firing state -- side-effect-free, safe to call for a dyno-style
        sweep or a test/calibration script."""
        scratch_cylinders = [Cylinder(phase_offset_deg=180.0 * i) for i in range(cyl_specs.CYLINDER_COUNT)]
        boost_pa = max(_supercharger_boost_pa(rpm), cyl_specs.TURBO_MAX_BOOST_PA if rpm > cyl_specs.TURBO_SPOOL_START_RPM else 0.0)
        effective_map_pa = cyl_specs.ATMOSPHERIC_PRESSURE_PA + boost_pa
        ve_frac = _volumetric_efficiency(rpm)
        afr_target = _target_afr(boost_pa, cyl_specs.STOICHIOMETRIC_AFR)  # calibration reference: baseline gasoline
        n_steps_per_cycle = 360  # 2 degrees per step across the full 720-degree cycle
        dtheta_deg = 720.0 / n_steps_per_cycle
        cycle_angle_deg = 0.0
        total_work_j = 0.0
        # Run 2 full cycles and only measure the second: a cylinder whose
        # phase offset starts it mid-cycle (e.g. already mid-combustion)
        # only gets partial credit within a single isolated 720-degree
        # window -- a real, continuously-running engine self-heals this in
        # a revolution or two (see Engine.__init__'s cylinders), but this
        # throwaway scratch sweep needs the first cycle discarded instead.
        for cycle in range(2):
            for _ in range(n_steps_per_cycle):
                for cyl in scratch_cylinders:
                    torque_nm, _ = cyl.step(cycle_angle_deg, dtheta_deg, effective_map_pa, ve_frac, afr_target,
                                             self.condition)
                    if cycle == 1:
                        total_work_j += torque_nm * np.radians(dtheta_deg)
                cycle_angle_deg = (cycle_angle_deg + dtheta_deg) % 720.0
        avg_indicated_torque_nm = total_work_j / np.radians(720.0)
        # Baseline electrical load only (no lights/HVAC assumed on) — the
        # most representative default for a dyno-style wide-open sweep.
        return avg_indicated_torque_nm - _friction_torque_nm(rpm) - self._accessory_load_torque_nm(rpm)

    def set_throttle(self, throttle):
        self.throttle = float(np.clip(throttle, 0.0, 1.0))

    def set_traction_control_limit(self, limit_frac):
        """A traction-control cut on delivered torque, 0..1 — real ECMs apply
        this exact kind of request (torque reduction via throttle/ignition/fuel),
        received from the TCS module over CAN in a real car. Applied here as a
        direct cut on effective manifold pressure (a fuel/spark/throttle cut all
        have the same net effect on trapped combustion energy at this level of
        model)."""
        self.traction_control_limit_frac = float(np.clip(limit_frac, 0.0, 1.0))

    def _combined_boost_pa(self, rpm):
        sc_boost_pa = _supercharger_boost_pa(rpm)
        # Real researched handoff (specs/cylinder.py): supercharger active
        # up to ~3650rpm, then the turbo takes over -- blended smoothly
        # over a narrow band rather than a hard rpm cutoff, for numerical
        # niceness (no discontinuity in commanded boost as rpm crosses it).
        band = 300.0
        sc_frac = np.clip((cyl_specs.SUPERCHARGER_DISENGAGE_RPM + band / 2.0 - rpm) / band, 0.0, 1.0)
        return sc_frac * sc_boost_pa + (1.0 - sc_frac) * self.turbocharger.boost_pa

    def _effective_map_pa(self, boost_pa):
        effective_throttle = max(self.throttle, cyl_specs.IDLE_AIR_CONTROL_MIN_THROTTLE_FRAC)
        idle_pa = cyl_specs.ATMOSPHERIC_PRESSURE_PA * cyl_specs.IDLE_MAP_FRACTION
        full_pa = cyl_specs.ATMOSPHERIC_PRESSURE_PA + boost_pa
        return idle_pa + effective_throttle * (full_pa - idle_pa)

    def _cylinder_torque_sum_nm(self, dtheta_deg, rpm):
        """One sub-step: computes this instant's boost/manifold-pressure/VE/AFR,
        advances every cylinder + the shared cycle-angle clock, returns the
        summed indicated torque (Nm) across all cylinders this sub-step."""
        boost_pa = self._combined_boost_pa(rpm) * (1.0 - self._fuel_boost_derate_frac)
        effective_map_pa = self._effective_map_pa(boost_pa)
        effective_map_pa *= self.traction_control_limit_frac  # TCS torque-reduction request
        self.manifold_pressure_pa = effective_map_pa

        self.egr_valve.step(rpm, self.throttle)
        self.pcv_valve.step(boost_pa)
        # EGR + PCV blow-by gas both physically displace fresh air in the
        # same manifold volume -- the real mechanism for both -- applied as
        # a combined derating of volumetric efficiency rather than a
        # separate dilution model. PCV's contribution is real but an order
        # of magnitude smaller than EGR's (see PCVValve).
        ve_frac = (_volumetric_efficiency(rpm) * (1.0 - self.egr_valve.flow_fraction)
                   * (1.0 - self.pcv_valve.ve_derate_fraction()))
        dilution_frac = self.egr_valve.flow_fraction + self.pcv_valve.ve_derate_fraction()
        afr_target = _target_afr(boost_pa, self._fuel_stoich_afr)
        backpressure_pa = self.exhaust_system.backpressure_pa()

        omega = rpm * 2.0 * np.pi / 60.0
        dt_sub = np.radians(dtheta_deg) / omega if omega > 0.0 else 0.0

        total_torque_nm = 0.0
        fuel_pressure_frac = self.fuel_pump.pressure_fraction
        for cyl, o2 in zip(self.cylinders, self.oxygen_sensors):
            torque_nm, fuel_trapped_kg = cyl.step(
                self.cycle_angle_deg, dtheta_deg, effective_map_pa, ve_frac, afr_target, self.condition,
                fuel_pressure_frac, backpressure_pa, dilution_frac,
                self._fuel_lhv_j_per_kg, self._fuel_combustion_efficiency,
            )
            total_torque_nm += torque_nm
            self.total_fuel_burned_kg += fuel_trapped_kg
            if fuel_trapped_kg > 0.0:
                o2.step(dt_sub, cyl.trapped_air_mass_kg / cyl.fuel_mass_kg)
        self.cycle_angle_deg = (self.cycle_angle_deg + dtheta_deg) % 720.0
        return total_torque_nm

    def step_unlocked(self, dt, load_torque_nm):
        """
        Advance engine state by dt seconds while the torque converter is
        unlocked: the crank is free to accelerate under its own inertia
        against the converter's hydraulic pump load.

        load_torque_nm: resistive torque presented by the converter pump, Nm.
        Any imbalance between what the engine produces and this load goes
        into accelerating (or decelerating) the crank itself. Sub-steps the
        real per-cylinder combustion + crank dynamics together (see
        specs.cylinder.CRANK_SUBSTEPS_PER_TICK) since a full combustion
        cycle can span more crank rotation than a single outer tick at
        higher rpm — an ordinary Euler step over the whole dt would alias
        right past entire combustion events.
        """
        self.turbocharger.step(dt, self.rpm, self.throttle)
        self.exhaust_system.step(dt, engine_running=True)
        self.fuel_pump_relay.set_energized(True)
        self.fuel_pump.set_running(self.fuel_pump_relay.contacts_closed)
        self.fuel_pump.step(dt)
        omega = self.omega
        idle_omega = specs.IDLE_RPM * 2.0 * np.pi / 60.0
        n_sub = _substep_count(omega, dt)
        dt_sub = dt / n_sub
        inertia = self.total_rotating_inertia_kgm2

        for _ in range(n_sub):
            rpm_now = omega * 60.0 / (2.0 * np.pi)
            dtheta_deg = np.degrees(omega * dt_sub)
            indicated_torque_nm = self._cylinder_torque_sum_nm(dtheta_deg, rpm_now)
            friction_torque_nm = _friction_torque_nm(rpm_now) + self._accessory_load_torque_nm(rpm_now)
            net_torque_nm = indicated_torque_nm - friction_torque_nm - load_torque_nm
            domega_dt = net_torque_nm / inertia
            omega = max(omega + domega_dt * dt_sub, idle_omega)

        self.rpm = min(omega * 60.0 / (2.0 * np.pi), specs.REDLINE_RPM)  # fuel cut at redline

    def step_off(self, dt):
        """
        Advance engine state while the ignition is off/accessory-only: no
        fuel/spark, so no indicated torque -- the crank spins down under its
        own internal friction rather than instantly stopping (a real engine
        takes a couple of seconds to come to rest after shutoff).
        """
        self.turbocharger.reset()
        self.exhaust_system.step(dt, engine_running=False)
        self.fuel_pump_relay.set_energized(False)
        self.fuel_pump.set_running(self.fuel_pump_relay.contacts_closed)
        self.fuel_pump.step(dt)
        domega_dt = -_friction_torque_nm(self.rpm) / self.total_rotating_inertia_kgm2
        new_omega = max(0.0, self.omega + domega_dt * dt)
        self.rpm = new_omega * 60.0 / (2.0 * np.pi)

    def step_cranking(self, dt, crank_time_s=specs.STARTER_CRANK_TIME_S):
        """Starter motor spins the crank up toward idle. crank_time_s defaults to a cold
        start's duration; pass AUTO_STOP_RESTART_TIME_S for the much quicker auto-stop restart."""
        self.fuel_pump_relay.set_energized(True)  # a real fuel pump primes before/during cranking, not after
        self.fuel_pump.set_running(self.fuel_pump_relay.contacts_closed)
        self.fuel_pump.step(dt)
        self.exhaust_system.step(dt, engine_running=False)  # not yet producing real exhaust flow
        self.rpm = min(specs.IDLE_RPM, self.rpm + (specs.IDLE_RPM / crank_time_s) * dt)

    def step_locked(self, dt, imposed_rpm):
        """
        Advance engine state by dt seconds while the torque converter's
        lockup clutch is engaged: crank speed is rigidly tied to the
        driveline (engine's own rotational inertia is treated as negligible
        next to the vehicle's, a standard simplification once locked).

        Returns net crank output torque (Nm) delivered straight into the driveline.
        """
        self.turbocharger.step(dt, imposed_rpm, self.throttle)
        self.exhaust_system.step(dt, engine_running=True)
        self.fuel_pump_relay.set_energized(True)
        self.fuel_pump.set_running(self.fuel_pump_relay.contacts_closed)
        self.fuel_pump.step(dt)
        self.rpm = float(np.clip(imposed_rpm, specs.IDLE_RPM, specs.REDLINE_RPM))
        omega = self.omega
        n_sub = _substep_count(omega, dt)
        dt_sub = dt / n_sub
        dtheta_deg = np.degrees(omega * dt_sub)

        total_indicated_nm = 0.0
        for _ in range(n_sub):
            total_indicated_nm += self._cylinder_torque_sum_nm(dtheta_deg, self.rpm)
        avg_indicated_nm = total_indicated_nm / n_sub
        return avg_indicated_nm - _friction_torque_nm(self.rpm) - self._accessory_load_torque_nm(self.rpm)
