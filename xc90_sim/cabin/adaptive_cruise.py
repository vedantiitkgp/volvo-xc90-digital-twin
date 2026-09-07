"""
Adaptive Cruise Control (ACC): forward radar + a follow-distance law layered
on top of the existing CruiseController speed-tracking controller.

This project has no actual traffic simulation (no other vehicles with real
positions), so — same pattern as BlindSpotMonitor/ParkingAssist — the lead
vehicle's distance and relative speed are a virtual sensor set from outside
rather than derived from real geometry. The follow-distance LAW itself is
real and connected: given a lead vehicle, it computes a genuine target speed
that CruiseController then tracks exactly like a manually-set cruise speed.
"""

from ..specs import adas as specs


class ForwardRadar:
    def __init__(self):
        self.lead_vehicle_distance_m = None  # None = no target detected
        self.lead_vehicle_relative_speed_mps = 0.0  # negative = closing

    def set_lead_vehicle(self, distance_m, relative_speed_mps):
        self.lead_vehicle_distance_m = distance_m
        self.lead_vehicle_relative_speed_mps = relative_speed_mps

    def clear_lead_vehicle(self):
        self.lead_vehicle_distance_m = None
        self.lead_vehicle_relative_speed_mps = 0.0

    def target_detected(self):
        return self.lead_vehicle_distance_m is not None and self.lead_vehicle_distance_m <= specs.RADAR_MAX_RANGE_M


class AdaptiveCruiseController:
    def __init__(self):
        self.follow_gap_setting = "medium"

    def set_follow_gap(self, setting):
        if setting not in specs.FOLLOW_TIME_GAP_S:
            raise ValueError(f"unknown follow-gap setting: {setting!r}, expected one of {tuple(specs.FOLLOW_TIME_GAP_S)}")
        self.follow_gap_setting = setting

    def effective_target_speed_mps(self, radar, driver_set_speed_mps, own_speed_mps):
        """Real ACC law: match the lead vehicle's speed while correcting the
        gap back toward the selected time-gap distance, but never command
        faster than the driver's own set speed (the "cruise" part still
        caps it, same as a real car)."""
        if not radar.target_detected():
            return driver_set_speed_mps

        time_gap_s = specs.FOLLOW_TIME_GAP_S[self.follow_gap_setting]
        desired_gap_m = max(specs.ACC_MIN_FOLLOW_DISTANCE_M, time_gap_s * max(0.0, own_speed_mps))
        gap_error_m = radar.lead_vehicle_distance_m - desired_gap_m

        lead_speed_mps = own_speed_mps + radar.lead_vehicle_relative_speed_mps
        target_mps = lead_speed_mps + specs.ACC_GAP_ERROR_GAIN * gap_error_m
        return max(0.0, min(driver_set_speed_mps, target_mps))
