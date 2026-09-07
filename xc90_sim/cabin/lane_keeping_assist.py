"""
Lane-keeping assist (Pilot-Assist-style steering nudge): a forward camera's
lane-position reading + a bounded corrective steering law.

Same externally-driven virtual-sensor pattern as ForwardRadar/BlindSpotMonitor
-- this project has no real lane geometry to derive lateral offset/heading
error from, so LaneCamera's readings are set from outside. The correction
law itself is real: a small, bounded proportional nudge blended with the
driver's own steering input, backing off entirely for a real driver input
large enough to look like a deliberate turn/lane change (same as how a real
Pilot Assist won't fight a driver who's actually steering).
"""

from ..specs import adas as specs


class LaneCamera:
    def __init__(self):
        self.lane_detected = False
        self.lateral_offset_m = 0.0  # + = drifting right of lane center
        self.heading_error_rad = 0.0  # + = pointed right of the lane direction

    def set_lane_state(self, detected, lateral_offset_m=0.0, heading_error_rad=0.0):
        self.lane_detected = detected
        self.lateral_offset_m = lateral_offset_m
        self.heading_error_rad = heading_error_rad


class LaneKeepingAssist:
    def __init__(self):
        self.enabled = False  # driver toggles Pilot Assist steering, like a real car

    def set_enabled(self, enabled):
        self.enabled = enabled

    def corrective_steering_deg(self, camera, manual_steer_deg, turn_signal_active):
        """Returns a corrective delta (deg) to add to the driver's own
        steering command, or 0.0 if assist shouldn't intervene this tick."""
        if not self.enabled or not camera.lane_detected:
            return 0.0
        if turn_signal_active:
            return 0.0  # driver's signaling an intentional lane change
        if abs(manual_steer_deg) >= specs.LKA_DRIVER_OVERRIDE_DEG:
            return 0.0  # a real driver steering input this large is an override

        correction_deg = -(
            specs.LKA_LATERAL_GAIN_DEG_PER_M * camera.lateral_offset_m
            + specs.LKA_HEADING_GAIN_DEG_PER_RAD * camera.heading_error_rad
        )
        return max(-specs.LKA_MAX_CORRECTIVE_DEG, min(specs.LKA_MAX_CORRECTIVE_DEG, correction_deg))
