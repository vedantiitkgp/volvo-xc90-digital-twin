"""
Brake booster: amplifies pedal effort into braking force using the
vacuum supplied by VacuumPump. Modeled as a real, if simplified, assist
fraction — degrades if the vacuum reservoir is depleted, the real "pedal
goes hard, stopping distance increases" symptom of insufficient vacuum
assist. Floors at a reduced, not-zero fraction: a real car with no
booster assist at all is still drivable, just much harder to stop.
"""

from ..specs import chassis as specs


class BrakeBooster:
    def assist_fraction(self, reservoir_vacuum_kpa):
        if reservoir_vacuum_kpa >= specs.VACUUM_MIN_FOR_FULL_ASSIST_KPA:
            return 1.0
        frac = reservoir_vacuum_kpa / specs.VACUUM_MIN_FOR_FULL_ASSIST_KPA
        return specs.UNBOOSTED_BRAKE_FRACTION + frac * (1.0 - specs.UNBOOSTED_BRAKE_FRACTION)
