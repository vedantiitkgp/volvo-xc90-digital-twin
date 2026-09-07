"""
ESC (Electronic Stability Control): compares actual yaw rate against a
kinematic reference (from steering angle + speed) and brakes an individual
wheel to correct the difference — the standard strategy real systems use
(e.g. Bosch ESP): brake the INSIDE REAR wheel for understeer (rotates the
nose into the turn), brake the OUTSIDE FRONT wheel for oversteer (resists
excess rotation).

Senses over the CAN bus like TractionControl/ABS. Actuates via an
*additive* brake torque request returned to the simulation — unlike ABS
(which only scales down torque the driver already commanded), ESC can
apply braking the driver never asked for, exactly as it does in a real car.
"""

import math

from ..specs import dsc as specs
from ..specs import steering as steering_specs
from ..specs import chassis as chassis_specs
from ..ecu.chassis_ecu import CHASSIS_DYNAMICS, VEHICLE_REF


class ESC:
    def __init__(self, bus):
        self._yaw_rate_rad_s = 0.0
        self._steering_wheel_deg = 0.0
        self._reference_speed_kph = 0.0
        bus.subscribe(CHASSIS_DYNAMICS.arbitration_id, self._on_dynamics)
        bus.subscribe(VEHICLE_REF.arbitration_id, self._on_reference)

    def _on_dynamics(self, frame):
        v = frame.message.decode(frame.data)
        self._yaw_rate_rad_s = math.radians(v["yaw_rate_deg_s"])
        self._steering_wheel_deg = v["steering_angle_deg"]

    def _on_reference(self, frame):
        self._reference_speed_kph = frame.message.decode(frame.data)["reference_speed_kph"]

    def corrective_brake_torques_nm(self):
        """Returns {corner: extra_brake_torque_nm} for at most one wheel, or {}."""
        v_mps = self._reference_speed_kph / 3.6
        if v_mps < specs.ESC_MIN_SPEED_MPS:
            return {}  # kinematic reference (and wheel-speed sensing) unreliable this slow

        front_wheel_angle_rad = math.radians(self._steering_wheel_deg / steering_specs.STEERING_RATIO)
        reference_yaw_rate = v_mps * front_wheel_angle_rad / chassis_specs.WHEELBASE_M

        error = self._yaw_rate_rad_s - reference_yaw_rate
        if abs(error) < specs.ESC_YAW_RATE_DEADBAND_RAD_S:
            return {}

        turning_left = front_wheel_angle_rad >= 0.0
        torque_nm = min(specs.ESC_MAX_BRAKE_TORQUE_NM, specs.ESC_BRAKE_GAIN_NM_PER_RAD_S * abs(error))

        if error < 0.0:
            # Understeer: rotating LESS than the reference -> brake inside rear.
            corner = "rl" if turning_left else "rr"
        else:
            # Oversteer: rotating MORE than the reference -> brake outside front.
            corner = "fr" if turning_left else "fl"

        return {corner: torque_nm}
