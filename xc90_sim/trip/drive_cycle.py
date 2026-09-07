"""
Synthetic drive-cycle generator: turns (distance, driving style) into a
target speed-vs-time profile, the same way EPA/WLTP test cycles are defined
(a time -> speed lookup table) — because this sim has no live routing/map
API to turn two real addresses into an actual road-speed trace. Point-to-
point routing (turns, real road curvature, speed limits, traffic) is not
modeled; this produces a representative, not a real, trip.
"""

import numpy as np

_KPH_TO_MPS = 1.0 / 3.6
_MPH_TO_MPS = 0.44704

_CITY_CRUISE_MPS = 25 * _MPH_TO_MPS
_CITY_ACCEL_S = 6.0
_CITY_CRUISE_S = 15.0
_CITY_DECEL_S = 5.0
_CITY_STOP_S = 3.0

_HIGHWAY_CRUISE_MPS = 70 * _MPH_TO_MPS
_HIGHWAY_ACCEL_S = 15.0
_HIGHWAY_DECEL_S = 12.0


class DriveCycle:
    """A piecewise-linear speed-vs-time target profile."""

    def __init__(self, time_speed_points):
        self.times_s = np.array([p[0] for p in time_speed_points])
        self.speeds_mps = np.array([p[1] for p in time_speed_points])

    @property
    def duration_s(self):
        return float(self.times_s[-1])

    def target_speed_mps(self, t_s):
        return float(np.interp(t_s, self.times_s, self.speeds_mps, left=self.speeds_mps[0], right=0.0))


def _add_city_block(points, t0, d0):
    """One accelerate/cruise/decelerate/stop block. Returns (new_t, new_distance)."""
    t, d = t0, d0
    points.append((t, points[-1][1] if points else 0.0))

    points.append((t + _CITY_ACCEL_S, _CITY_CRUISE_MPS))
    d += 0.5 * _CITY_CRUISE_MPS * _CITY_ACCEL_S
    t += _CITY_ACCEL_S

    points.append((t + _CITY_CRUISE_S, _CITY_CRUISE_MPS))
    d += _CITY_CRUISE_MPS * _CITY_CRUISE_S
    t += _CITY_CRUISE_S

    points.append((t + _CITY_DECEL_S, 0.0))
    d += 0.5 * _CITY_CRUISE_MPS * _CITY_DECEL_S
    t += _CITY_DECEL_S

    points.append((t + _CITY_STOP_S, 0.0))
    t += _CITY_STOP_S

    return t, d


def _add_highway_leg(points, t0, d0, target_d):
    """Accelerate to highway cruise, hold as long as needed to hit target_d, then decelerate."""
    t, d = t0, d0
    accel_d = 0.5 * _HIGHWAY_CRUISE_MPS * _HIGHWAY_ACCEL_S
    decel_d = 0.5 * _HIGHWAY_CRUISE_MPS * _HIGHWAY_DECEL_S
    cruise_d = max(0.0, (target_d - d) - accel_d - decel_d)
    cruise_s = cruise_d / _HIGHWAY_CRUISE_MPS if _HIGHWAY_CRUISE_MPS > 0 else 0.0

    points.append((t + _HIGHWAY_ACCEL_S, _HIGHWAY_CRUISE_MPS))
    t += _HIGHWAY_ACCEL_S
    d += accel_d

    points.append((t + cruise_s, _HIGHWAY_CRUISE_MPS))
    t += cruise_s
    d += cruise_d

    points.append((t + _HIGHWAY_DECEL_S, 0.0))
    t += _HIGHWAY_DECEL_S
    d += decel_d

    return t, d


def build_drive_cycle(distance_km, style="mixed"):
    """
    style: 'city' (repeating stop-and-go blocks), 'highway' (one sustained
    cruise), or 'mixed' (city blocks at each end, highway stretch between).
    """
    target_d = distance_km * 1000.0
    points = [(0.0, 0.0)]
    t, d = 0.0, 0.0

    if style == "city":
        while d < target_d:
            t, d = _add_city_block(points, t, d)

    elif style == "highway":
        t, d = _add_highway_leg(points, t, d, target_d)

    elif style == "mixed":
        end_city_reserve_d = min(target_d * 0.3, 2 * (0.5 * _CITY_CRUISE_MPS * (_CITY_ACCEL_S + _CITY_DECEL_S) + _CITY_CRUISE_MPS * _CITY_CRUISE_S))
        # Leading city blocks (up to ~15% of trip distance).
        while d < target_d * 0.15:
            t, d = _add_city_block(points, t, d)
        # Highway stretch covers the middle, reserving distance for trailing city blocks.
        t, d = _add_highway_leg(points, t, d, target_d - end_city_reserve_d)
        # Trailing city blocks to close out the trip.
        while d < target_d:
            t, d = _add_city_block(points, t, d)

    else:
        raise ValueError(f"unknown drive cycle style: {style!r}")

    return DriveCycle(points), d
