"""
2016 XC90 steering — spec constants.

Electric power-assisted rack and pinion, 2.8 turns lock-to-lock (published
spec), 12.1 m curb-to-curb turning circle (published spec). Volvo doesn't
publish an overall steering ratio directly, so it's derived below from the
turning circle + wheelbase via the standard single-track (bicycle model)
turning-radius relation — this is a calculation from two real spec numbers,
not a free-standing guess, though it does carry the small approximation of
treating the curb-to-curb radius as the centerline turning radius.
"""

import math

from . import chassis as _chassis

TURNING_CIRCLE_CURB_M = 12.1  # published spec, curb-to-curb diameter
LOCK_TO_LOCK_TURNS = 2.8      # published spec

_turning_radius_m = TURNING_CIRCLE_CURB_M / 2.0
_max_front_wheel_angle_rad = math.atan(_chassis.WHEELBASE_M / _turning_radius_m)
MAX_FRONT_WHEEL_ANGLE_DEG = math.degrees(_max_front_wheel_angle_rad)

MAX_STEERING_WHEEL_ANGLE_DEG = LOCK_TO_LOCK_TURNS * 360.0 / 2.0  # from center to one lock
STEERING_RATIO = MAX_STEERING_WHEEL_ANGLE_DEG / MAX_FRONT_WHEEL_ANGLE_DEG
