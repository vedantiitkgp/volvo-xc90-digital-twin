"""5th-gen Haldex electrohydraulic AWD: front/rear axle torque split."""

import numpy as np

from ..specs import awd as specs


class HaldexAWD:
    """
    Splits driveshaft torque between front and rear axles using two
    combined mechanisms, matching how a real Gen 3+ Haldex unit behaves:
      - reactive: shifts toward the rear as front/rear speed difference
        (already-occurring slip) grows
      - proactive: pre-tensions the clutch toward the rear based on
        anticipated demand (throttle position at low speed) even before
        any slip has actually developed
    Whichever mechanism calls for more rear engagement at a given instant wins.
    """

    def __init__(self):
        self.front_bias = specs.BASE_FRONT_BIAS  # last computed split, for telemetry/CAN

    def split(self, total_torque_nm, front_axle_omega, rear_axle_omega, throttle, vehicle_speed_mps):
        """Returns (front_axle_torque_nm, rear_axle_torque_nm)."""
        slip = abs(front_axle_omega - rear_axle_omega)
        slip_frac = np.clip(slip / specs.SLIP_FOR_MIN_BIAS_RAD_S, 0.0, 1.0)
        reactive_bias = specs.BASE_FRONT_BIAS - slip_frac * (specs.BASE_FRONT_BIAS - specs.MIN_FRONT_BIAS)

        speed_frac = np.clip(1.0 - vehicle_speed_mps / specs.PROACTIVE_SPEED_THRESHOLD_MPS, 0.0, 1.0)
        anticipated_frac = np.clip(throttle, 0.0, 1.0) * speed_frac
        proactive_bias = specs.BASE_FRONT_BIAS - anticipated_frac * (specs.BASE_FRONT_BIAS - specs.MIN_FRONT_BIAS)

        self.front_bias = min(reactive_bias, proactive_bias)

        front_torque = total_torque_nm * self.front_bias
        rear_torque = total_torque_nm * (1.0 - self.front_bias)
        return front_torque, rear_torque
