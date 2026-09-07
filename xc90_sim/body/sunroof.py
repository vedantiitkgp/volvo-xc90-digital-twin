"""
Panoramic sunroof: the glass panel (closed/vent/open) and the electric
sunshade/cover move independently but with a real mechanical interlock —
the glass panel retracts into the same space the shade occupies, so a real
sunroof can't open the glass with the shade closed (it forces the shade
open first) or close the shade while the glass isn't closed. Both actuate
on a timed cycle, same technique as the power tailgate.
"""

from ..specs import body as specs

GLASS_STATES = ("closed", "vent", "open")


class Sunroof:
    def __init__(self):
        self.glass_state = "closed"
        self.shade_open = False
        self._glass_target = "closed"
        self._glass_progress_s = 0.0
        self._shade_target_open = False
        self._shade_progress_s = 0.0

    def request_glass(self, state):
        if state not in GLASS_STATES:
            raise ValueError(f"unknown sunroof glass state: {state!r}, expected one of {GLASS_STATES}")
        if state == "open" and not self.shade_open:
            self.request_shade(True)  # mechanical interlock: shade must be open first
        self._glass_target = state
        self._glass_progress_s = 0.0

    def request_shade(self, open_):
        if not open_ and self.glass_state != "closed":
            return  # can't close the shade while the glass isn't fully closed
        self._shade_target_open = open_
        self._shade_progress_s = 0.0

    def glass_target(self):
        return self._glass_target

    def glass_progress_frac(self):
        """0..1 through the real timed glass actuation -- 1.0 whenever the
        glass is already at its target (not mid-cycle)."""
        if self.glass_state == self._glass_target:
            return 1.0
        return min(1.0, self._glass_progress_s / specs.SUNROOF_GLASS_ACTUATION_TIME_S)

    def shade_target(self):
        return self._shade_target_open

    def shade_progress_frac(self):
        """0..1 through the real timed shade actuation -- 1.0 whenever the
        shade is already at its target (not mid-cycle)."""
        if self.shade_open == self._shade_target_open:
            return 1.0
        return min(1.0, self._shade_progress_s / specs.SUNROOF_SHADE_ACTUATION_TIME_S)

    def step(self, dt):
        if self.glass_state != self._glass_target:
            self._glass_progress_s += dt
            if self._glass_progress_s >= specs.SUNROOF_GLASS_ACTUATION_TIME_S:
                self.glass_state = self._glass_target
                self._glass_progress_s = 0.0
        if self.shade_open != self._shade_target_open:
            self._shade_progress_s += dt
            if self._shade_progress_s >= specs.SUNROOF_SHADE_ACTUATION_TIME_S:
                self.shade_open = self._shade_target_open
                self._shade_progress_s = 0.0
