"""
Blind Spot Information System (BLIS — Volvo's own real feature/name): warns
of a vehicle detected in the driver's blind spot on either side. Like real
BLIS, inactive below a minimum speed (parking-lot-speed false positives
aren't useful) — gating happens in Simulation.step(), not stored here, so
this class stays a plain sensor-state model.
"""

from ..specs import cabin as specs


class BlindSpotMonitor:
    def __init__(self):
        self.enabled = True
        self.left_occupied = False
        self.right_occupied = False

    def set_left_occupied(self, occupied):
        self.left_occupied = occupied

    def set_right_occupied(self, occupied):
        self.right_occupied = occupied

    def left_warning(self, vehicle_speed_mps):
        return self.enabled and self.left_occupied and abs(vehicle_speed_mps) >= specs.BLIS_MIN_SPEED_MPS

    def right_warning(self, vehicle_speed_mps):
        return self.enabled and self.right_occupied and abs(vehicle_speed_mps) >= specs.BLIS_MIN_SPEED_MPS
