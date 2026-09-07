"""
Park Assist Pilot: semi-autonomous parallel parking. Scans for a gap while
driving past (a side-facing distance sensor, separate from the front/rear
ParkingAssist sensors used for ordinary park-in/park-out warnings), then,
once engaged in Reverse, steers itself through a real, simplified two-phase
parallel-park maneuver -- turn to full lock, reverse to an angle, then
countersteer to full lock and straighten -- while the driver's own steering
input is overridden (Simulation reads steering_command_deg() instead, while
a phase is active). The driver can cancel at any time and take back full
control, same as the real feature.

This is a genuine, geometrically-motivated technique (the same one driving
instruction describes for a human doing this by hand), not Volvo's actual
(proprietary, unpublished) path-planning algorithm — see specs/cabin.py for
the full caveat.
"""

import math

from ..specs import cabin as specs

PHASES = ("idle", "scanning", "gap_found", "phase1_turn_in", "phase2_straighten", "complete", "aborted")


class ParkAssistPilot:
    def __init__(self):
        self.phase = "idle"
        self.scan_side = None  # 'left' or 'right'
        self.found_gap_length_m = None
        self._gap_open_since_m = None
        self._side_distance_m = None
        self._initial_heading_rad = None

    def start_scanning(self, side):
        self.phase = "scanning"
        self.scan_side = side
        self.found_gap_length_m = None
        self._gap_open_since_m = None

    def set_side_obstacle_distance_m(self, distance_m):
        """distance_m: None if nothing detected within sensor range (a gap)."""
        self._side_distance_m = distance_m

    def cancel(self):
        """The driver taking back control, at any phase — always honored."""
        self.phase = "idle"
        self.scan_side = None

    def engage(self, current_heading_rad):
        """Starts the actual steering maneuver. Caller (Simulation) must
        already have checked the gear selector is in Reverse — a real Park
        Assist Pilot only steers while backing into the spot."""
        if self.phase != "gap_found":
            return False
        self.phase = "phase1_turn_in"
        self._initial_heading_rad = current_heading_rad
        return True

    def is_maneuvering(self):
        return self.phase in ("phase1_turn_in", "phase2_straighten")

    def _curb_sign(self):
        """SAE convention (positive = left, matching SteeringSystem): parking
        into a gap on the right means steering right (negative) to turn in."""
        return 1.0 if self.scan_side == "left" else -1.0

    def steering_command_deg(self, max_wheel_angle_deg):
        if self.phase == "phase1_turn_in":
            return self._curb_sign() * max_wheel_angle_deg
        if self.phase == "phase2_straighten":
            return -self._curb_sign() * max_wheel_angle_deg
        return 0.0

    def step(self, distance_traveled_m, current_heading_rad, front_distance_m, rear_distance_m):
        if self.phase == "scanning":
            self._update_scan(distance_traveled_m)
            return

        if not self.is_maneuvering():
            return

        # Safety abort: something's gotten dangerously close during the
        # maneuver — hand control straight back to the driver, same as a
        # real system would rather than blindly continuing a planned path.
        if (front_distance_m is not None and front_distance_m < specs.PARK_SENSOR_CRITICAL_M) or \
                (rear_distance_m is not None and rear_distance_m < specs.PARK_SENSOR_CRITICAL_M):
            self.phase = "aborted"
            return

        progress_deg = abs(math.degrees(current_heading_rad - self._initial_heading_rad))
        if self.phase == "phase1_turn_in" and progress_deg >= specs.PARK_PILOT_PHASE1_HEADING_DEG:
            self.phase = "phase2_straighten"
        elif self.phase == "phase2_straighten" and progress_deg <= specs.PARK_PILOT_COMPLETE_HEADING_TOLERANCE_DEG:
            self.phase = "complete"

    def _update_scan(self, distance_traveled_m):
        occupied = self._side_distance_m is not None and self._side_distance_m <= specs.PARK_PILOT_SCAN_RANGE_M
        if occupied:
            if self._gap_open_since_m is not None:
                gap_length = distance_traveled_m - self._gap_open_since_m
                if gap_length >= specs.PARK_PILOT_MIN_SPOT_LENGTH_M:
                    self.found_gap_length_m = gap_length
                    self.phase = "gap_found"
            self._gap_open_since_m = None
        elif self._gap_open_since_m is None:
            self._gap_open_since_m = distance_traveled_m
