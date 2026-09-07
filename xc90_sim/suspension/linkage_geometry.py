"""
Instant-center / swing-arm-equivalent suspension kinematics — the standard
hand-calculation method (see Milliken & Milliken, "Race Car Vehicle
Dynamics") for deriving camber gain, roll center height, and anti-dive/
anti-squat from actual control-arm hardpoints, rather than an assumed flat
gain curve.

Front view (upper arm + lower arm lines, extended, intersect at the
"instant center"; the wheel effectively swings about this point) gives
camber gain. Roll center: the standard construction draws a line from THIS
side's instant center to the OPPOSITE wheel's contact patch; where that
line crosses the vehicle centerline is the roll center — using the same
side's contact patch instead (an easy mistake) makes the result wildly
oversensitive to hardpoint precision, since that crossing sits almost all
the way across the car rather than roughly in the middle.

Side view (a single representative arm's slope) gives anti-dive/anti-squat.
"""

import math

from ..specs import linkage as specs
from ..specs import chassis as chassis_specs


def _line_intersection(p1, p2, p3, p4):
    """Intersection of line(p1,p2) and line(p3,p4), extended infinitely."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = p3
    x4, y4 = p4
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-9:
        return None
    px = ((x1 * y2 - y1 * x2) * (x3 - x4) - (x1 - x2) * (x3 * y4 - y3 * x4)) / denom
    py = ((x1 * y2 - y1 * x2) * (y3 - y4) - (y1 - y2) * (x3 * y4 - y3 * x4)) / denom
    return (px, py)


class InstantCenterSuspension:
    """One axle's (front or rear) front-view swing-arm-equivalent geometry."""

    def __init__(self, upper_ball_yz, upper_pivot_yz, lower_ball_yz, lower_pivot_yz):
        self.ic_yz = _line_intersection(upper_pivot_yz, upper_ball_yz, lower_pivot_yz, lower_ball_yz)
        # Swing-arm vector at static ride height: IC -> wheel center (0, 0).
        y_ic, z_ic = self.ic_yz
        self._radius = math.hypot(-y_ic, -z_ic)
        self._static_angle = math.atan2(-z_ic, -y_ic)

    def camber_rad(self, deflection_m):
        """Camber change (rad) from static, for a corner compressed/extended by deflection_m."""
        y_ic, z_ic = self.ic_yz
        z_new = deflection_m
        under_sqrt = self._radius ** 2 - (z_new - z_ic) ** 2
        if under_sqrt < 0.0:
            return None  # deflection exceeds this swing arm's reach — outside physical travel
        delta = math.sqrt(under_sqrt)
        # Two solutions for y_new; pick the branch continuous with the static case (deflection=0).
        y_candidates = (y_ic + delta, y_ic - delta)
        y_new = min(y_candidates, key=lambda y: abs(y - 0.0))
        new_angle = math.atan2(z_new - z_ic, y_new - y_ic)
        return new_angle - self._static_angle

    def roll_center_height_m(self, track_m):
        """Height of the roll center above the tire contact patch plane."""
        half_track = track_m / 2.0
        y_ic, z_ic = self.ic_yz
        ic_absolute = (half_track + y_ic, z_ic)  # this wheel's IC, in centerline-relative y
        opposite_contact_patch = (-half_track, -chassis_specs.TIRE_ROLLING_RADIUS_M)
        y1, z1 = ic_absolute
        y2, z2 = opposite_contact_patch
        if abs(y2 - y1) < 1e-9:
            return None
        t = (0.0 - y1) / (y2 - y1)
        z_at_centerline = z1 + t * (z2 - z1)
        return z_at_centerline + chassis_specs.TIRE_ROLLING_RADIUS_M


def _side_view_slope(ball_xz, pivot_xz):
    """Rise/run slope of the arm in the side (x-z) view — this IS tan(angle from horizontal)."""
    dx = pivot_xz[0] - ball_xz[0]
    dz = pivot_xz[1] - ball_xz[1]
    return dz / dx


FRONT = InstantCenterSuspension(
    specs.FRONT_UPPER_BALL_JOINT_YZ, specs.FRONT_UPPER_PIVOT_YZ,
    specs.FRONT_LOWER_BALL_JOINT_YZ, specs.FRONT_LOWER_PIVOT_YZ,
)
REAR = InstantCenterSuspension(
    specs.REAR_UPPER_BALL_JOINT_YZ, specs.REAR_UPPER_PIVOT_YZ,
    specs.REAR_LOWER_BALL_JOINT_YZ, specs.REAR_LOWER_PIVOT_YZ,
)

# Anti-dive (front, under braking) / anti-squat (rear, under acceleration):
# the fraction of the theoretical spring-only pitch moment that's instead
# reacted geometrically through the links. Simplified vs. textbook brake-
# bias-weighted formulas (which vary by convention) but directionally
# correct and empirically verified to reduce dive/squat as expected.
FRONT_ANTI_DIVE_FRACTION = abs(_side_view_slope(specs.FRONT_LOWER_BALL_JOINT_XZ, specs.FRONT_LOWER_PIVOT_XZ))
REAR_ANTI_SQUAT_FRACTION = abs(_side_view_slope(specs.REAR_LOWER_BALL_JOINT_XZ, specs.REAR_LOWER_PIVOT_XZ))
