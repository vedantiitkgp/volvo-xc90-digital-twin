"""
Suspension kinematics: camber and toe as a function of corner compression.

Camber is now derived from actual 3D linkage hardpoints via the instant-
center/swing-arm method (see linkage_geometry.py) — a real double-wishbone
(front) or multi-link (rear) linkage's full 3D geometry gets characterized
this way in practice. Toe remains a simple linear gain: a dedicated toe-
control link's behavior isn't captured by the 2-arm swing-arm model used
for camber/roll-center, so a flat "bump steer" gain is used instead, the
same simplification professional K&C summaries often use for toe curves.
"""

import math

from ..specs import suspension as specs
from . import linkage_geometry


def camber_rad(corner, deflection_m):
    """corner: 'fl'|'fr'|'rl'|'rr'. deflection_m: compression beyond static, +down."""
    geometry = linkage_geometry.FRONT if corner[0] == "f" else linkage_geometry.REAR
    change = geometry.camber_rad(deflection_m)
    if change is None:
        change = 0.0  # deflection beyond the swing arm's reach — shouldn't happen within bump/droop travel
    # linkage_geometry's raw sign (positive in bump) is flipped here to match
    # this module's established convention (negative camber gain in bump).
    return -change


def toe_rad(corner, deflection_m):
    """
    Returns the kinematic toe contribution to this wheel's steer angle, in
    the same sign convention as SteeringSystem (positive = turns the car
    left). Toe-IN under bump means the LEFT wheel points slightly right
    (negative) and the RIGHT wheel points slightly left (positive).
    """
    gain = specs.FRONT_TOE_GAIN_DEG_PER_M if corner[0] == "f" else specs.REAR_TOE_GAIN_DEG_PER_M
    toe_in_magnitude = math.radians(gain * deflection_m)
    is_left = corner[1] == "l"
    return -toe_in_magnitude if is_left else toe_in_magnitude
