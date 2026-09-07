"""
Intake/exhaust valve: a real lift curve (raised-cosine profile — the
standard simplified shape when the real cam profile isn't published) as a
function of this cylinder's own crank angle, not just an open/closed
boolean. Camshaft.py owns the actual intake/exhaust Valve instances for a
cylinder and delegates to them.
"""

import math


class Valve:
    def __init__(self, open_deg, close_deg, max_lift_mm):
        """open_deg/close_deg: this cylinder's own 0-720 degree angle at which
        the valve opens/closes — close_deg < open_deg means the window wraps
        past the 720/0 boundary (real for both intake and exhaust here)."""
        self.open_deg = open_deg
        self.close_deg = close_deg
        self.max_lift_mm = max_lift_mm

    def _duration_deg(self):
        if self.close_deg >= self.open_deg:
            return self.close_deg - self.open_deg
        return (720.0 - self.open_deg) + self.close_deg

    def is_open(self, cylinder_angle_deg):
        if self.close_deg >= self.open_deg:
            return self.open_deg <= cylinder_angle_deg <= self.close_deg
        return cylinder_angle_deg >= self.open_deg or cylinder_angle_deg <= self.close_deg

    def lift_mm(self, cylinder_angle_deg):
        if not self.is_open(cylinder_angle_deg):
            return 0.0
        if cylinder_angle_deg >= self.open_deg:
            progress_deg = cylinder_angle_deg - self.open_deg
        else:
            progress_deg = (720.0 - self.open_deg) + cylinder_angle_deg
        frac = progress_deg / self._duration_deg()
        return self.max_lift_mm * math.sin(math.pi * frac) ** 2
