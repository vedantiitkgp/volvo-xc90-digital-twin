"""
12V battery (AGM — real, well-known requirement for a car with genuine
Auto Start/Stop; a flooded lead-acid battery wears out prematurely under
that much engine-off/restart cycling). Charges (a small maintenance
trickle beyond immediate demand) while the alternator is actually
supplying power (engine running); discharges to cover electrical demand
otherwise (ignition accessory-only, or the real current spike a starter
motor draws while cranking) — including a genuine failure mode: too weak
to crank, the same way a real dead battery behaves.

This car actually carries TWO of these (real, confirmed — see
specs.SUPPORT_BATTERY_CAPACITY_AH): a main starter battery and a smaller
support/auxiliary battery, both modeled with this same class (see
Simulation, which constructs a second Battery(capacity_ah=...) and routes
cranking-load current to keep the starter's draw off the electronics-bus
battery — the real reason a second battery exists on a car with this much
engine-restart cycling).
"""

from ..specs import accessories as specs


class Battery:
    def __init__(self, charge_frac=0.9, capacity_ah=None):
        """capacity_ah: defaults to the main starter battery's capacity —
        pass specs.SUPPORT_BATTERY_CAPACITY_AH to model this car's smaller
        second (support/auxiliary) battery with the same class."""
        self.charge_frac = charge_frac
        self.capacity_ah = capacity_ah if capacity_ah is not None else specs.BATTERY_CAPACITY_AH
        # Physically disconnected (terminal pulled) -- a real, connected
        # state distinct from just being discharged: no current flows in
        # either direction at all, same as an actual disconnected battery.
        self.disconnected = False

    def set_disconnected(self, disconnected):
        self.disconnected = disconnected

    def step(self, dt, net_power_w):
        """net_power_w: positive = charging, negative = discharging."""
        if self.disconnected:
            return
        capacity_j = self.capacity_ah * specs.BATTERY_NOMINAL_VOLTAGE * 3600.0
        self.charge_frac = max(0.0, min(1.0, self.charge_frac + (net_power_w * dt) / capacity_j))

    def low_charge_warning(self):
        return self.charge_frac <= specs.BATTERY_LOW_CHARGE_WARNING_FRAC

    def can_crank(self):
        return not self.disconnected and self.charge_frac >= specs.MIN_CHARGE_FRAC_TO_START
