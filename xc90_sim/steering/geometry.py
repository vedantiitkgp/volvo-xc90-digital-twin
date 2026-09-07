"""Steering wheel input -> road wheel angles, with Ackermann correction."""

import math

from ..specs import steering as specs
from ..specs import chassis as chassis_specs
from ..specs import suspension as suspension_specs


class SteeringSystem:
    def __init__(self):
        self.wheel_angle_deg = 0.0  # driver steering wheel input

    def set_wheel_angle_deg(self, angle_deg):
        limit = specs.MAX_STEERING_WHEEL_ANGLE_DEG
        self.wheel_angle_deg = max(-limit, min(limit, angle_deg))

    def average_front_steer_angle_rad(self):
        """The single-track (bicycle model) equivalent front steer angle."""
        return math.radians(self.wheel_angle_deg / specs.STEERING_RATIO)

    def ackermann_wheel_angles_rad(self):
        """
        Returns (inner_wheel_angle_rad, outer_wheel_angle_rad) for the actual
        left/right front wheels, which must turn at slightly different angles
        so both trace circles about the same center (Ackermann geometry).
        Positive average angle = left turn (SAE convention): left wheel is
        inner, right wheel is outer.
        """
        avg_angle = self.average_front_steer_angle_rad()
        if abs(avg_angle) < 1e-6:
            return 0.0, 0.0

        turn_radius = chassis_specs.WHEELBASE_M / math.tan(abs(avg_angle))
        half_track = suspension_specs.FRONT_TRACK_M / 2.0
        inner_angle = math.atan(chassis_specs.WHEELBASE_M / (turn_radius - half_track))
        outer_angle = math.atan(chassis_specs.WHEELBASE_M / (turn_radius + half_track))

        sign = 1.0 if avg_angle > 0 else -1.0
        return sign * inner_angle, sign * outer_angle

    def left_right_wheel_angles_rad(self):
        """
        Returns (left_wheel_angle_rad, right_wheel_angle_rad). Positive
        average steer angle is a left turn (SAE convention), so the left
        wheel is the inner (sharper-angle) wheel and the right is outer;
        negative (right turn) swaps which physical wheel is inner.
        """
        inner_angle, outer_angle = self.ackermann_wheel_angles_rad()
        if self.average_front_steer_angle_rad() >= 0.0:
            return inner_angle, outer_angle  # left turn: left wheel is inner
        return outer_angle, inner_angle  # right turn: left wheel is outer
