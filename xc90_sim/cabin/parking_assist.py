"""
Parking assist (front/rear ultrasonic "Park Assist" sensors): distance-to-
obstacle -> warning zone -> tone interval, same information a real system
gives the driver. No automated parking maneuver/steering — that's a
separate, much larger robotics problem and out of scope here; this only
covers the sensor/warning layer, useful for both "parking in" (reversing
into a spot, rear sensors) and "parking out" (front sensors if nose-in).
"""

from ..specs import cabin as specs


class ParkingAssist:
    def __init__(self):
        self.enabled = True
        self.front_distance_m = None  # None = no obstacle detected / out of range
        self.rear_distance_m = None

    def set_front_obstacle_distance_m(self, distance_m):
        self.front_distance_m = distance_m

    def set_rear_obstacle_distance_m(self, distance_m):
        self.rear_distance_m = distance_m

    def clear_obstacles(self):
        self.front_distance_m = None
        self.rear_distance_m = None

    def _zone(self, distance_m):
        if not self.enabled or distance_m is None or distance_m > specs.PARK_SENSOR_MAX_RANGE_M:
            return "none"
        if distance_m < specs.PARK_SENSOR_CRITICAL_M:
            return "critical"
        if distance_m < specs.PARK_SENSOR_NEAR_M:
            return "near"
        return "far"

    def front_zone(self):
        return self._zone(self.front_distance_m)

    def rear_zone(self):
        return self._zone(self.rear_distance_m)

    def tone_interval_s(self, zone):
        """Real park-assist behavior: beep faster as the gap closes, solid tone at critical."""
        return {"none": None, "far": 0.8, "near": 0.3, "critical": 0.0}[zone]
