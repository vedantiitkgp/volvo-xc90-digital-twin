"""
Oil life monitor: counts down from 100% based on miles driven since the
last reset — a real oil life monitor is NOT a continuous oil-quality
sensor most cars don't have, it's a mileage (sometimes plus a driving-
severity factor, not modeled here) countdown a technician resets via a
service menu after an actual oil change, same as this project's own
service_history.py pattern for other components. Defaults to fresh (0
miles since reset) since no oil-change events exist in service_history.py
to initialize from — this project's CARFAX source often doesn't capture
quick-lube oil changes, so there's no real data to seed a "last changed"
mileage from; assuming fresh rather than fabricating one.
"""

from ..specs import cabin as specs


class OilLifeMonitor:
    def __init__(self):
        self.miles_since_reset = 0.0

    def reset(self):
        """The service-menu action a technician performs after an actual oil change."""
        self.miles_since_reset = 0.0

    def add_miles(self, miles):
        self.miles_since_reset += max(0.0, miles)

    def life_pct(self):
        return max(0.0, 100.0 * (1.0 - self.miles_since_reset / specs.OIL_LIFE_INTERVAL_MILES))

    def change_due(self):
        return self.life_pct() <= specs.OIL_LIFE_WARNING_PCT
