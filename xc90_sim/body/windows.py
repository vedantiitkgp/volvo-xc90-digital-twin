"""
Power windows: one per door, 0 (fully closed) .. 100 (fully open), moving at
a constant rate toward a requested target — unlike the power tailgate (a
fixed-duration full-cycle actuator), a real window motor moves at roughly
constant speed regardless of how far it has to travel, so this is rate-based
rather than a total-cycle timer.
"""

from ..specs import body as specs


class Windows:
    def __init__(self):
        self.position_pct = {corner: 0.0 for corner in specs.DOORS}
        self._target_pct = dict(self.position_pct)

    def request_position(self, corner, target_pct):
        """target_pct: 0 (closed) .. 100 (fully open). One-touch full up/down
        is just request_position(corner, 0) / request_position(corner, 100)."""
        self._target_pct[corner] = max(0.0, min(100.0, target_pct))

    def step(self, dt):
        max_step = specs.WINDOW_MOVE_RATE_PCT_PER_S * dt
        for corner in specs.DOORS:
            delta = self._target_pct[corner] - self.position_pct[corner]
            self.position_pct[corner] += max(-max_step, min(max_step, delta))

    def any_open(self):
        return any(pct > 0.5 for pct in self.position_pct.values())
