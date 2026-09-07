"""
Alternator: converts crank rotation (via the accessory/serpentine belt)
into electrical power. The real, genuinely-connected coupling this buys:
electrical demand from headlights, HVAC blower, seat heaters,
infotainment, wipers, and the fuel pump itself determines how much
mechanical torque the alternator draws from the crank — turning on the
headlights and heated seats genuinely (if subtly) loads the engine, same
as it does in a real car, rather than accessory load being one fixed
made-up constant regardless of what's actually switched on.
"""

from ..specs import accessories as specs


class Alternator:
    def load_torque_nm(self, omega_rad_s, electrical_demand_w, belt_condition=1.0):
        if omega_rad_s <= 1.0:
            return 0.0
        # A worn/slipping belt (low condition) transmits power less
        # efficiently -- a real, if usually minor, effect.
        effective_efficiency = specs.ALTERNATOR_EFFICIENCY * max(0.5, belt_condition)
        mechanical_power_w = electrical_demand_w / effective_efficiency
        return mechanical_power_w / omega_rad_s
