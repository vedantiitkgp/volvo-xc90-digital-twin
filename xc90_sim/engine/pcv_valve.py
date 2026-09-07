"""
PCV (Positive Crankcase Ventilation) valve: routes blow-by gas — exhaust
gas that leaks past the piston rings into the crankcase during combustion
— back into the intake to be burned, rather than vented to atmosphere (a
real, federally-mandated emissions system on every gasoline car since the
1960s). Blow-by rate genuinely increases with engine wear (worn rings
seal less well) and with cylinder pressure (higher under boost) — both
real, physical drivers, not a flat constant. The recirculated flow is
real but small (an order of magnitude below EGR's), so its intake-
dilution effect is modeled the same way EGR's is (displacing a small
fraction of fresh intake air) but with a much smaller derating.
"""

from ..specs import cylinder as specs


class PCVValve:
    def __init__(self, condition=1.0):
        """condition: engine wear condition (1.0 = fresh) — see xc90_sim.wear."""
        self.condition = condition
        self.blowby_flow_fraction = 0.0

    def step(self, boost_pa):
        wear_factor = 1.0 + (1.0 - self.condition) * specs.PCV_MAX_WEAR_BLOWBY_INCREASE_FRAC
        boost_factor = 1.0 + max(0.0, boost_pa) / specs.ATMOSPHERIC_PRESSURE_PA
        self.blowby_flow_fraction = specs.PCV_BASE_BLOWBY_FRACTION * wear_factor * boost_factor

    def ve_derate_fraction(self):
        return self.blowby_flow_fraction
