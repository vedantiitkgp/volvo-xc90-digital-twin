"""
Chassis/body control module: wheel speeds, body dynamics, brake pedal.

Wheel speed is broadcast per corner (FL/FR/RL/RR) from the sim's genuine
per-wheel model — these can differ from each other now (cornering, one
wheel spinning under the open differential), same as a real ABS module's
signal set would show. Each corner has its own WheelSpeedSensor (pulse
quantization + noise), not the physics engine's exact omega.
"""

import math
import statistics

from ..network import CANMessage, CANSignal
from ..specs import chassis as chassis_specs
from .base import ECU
from .wheel_speed_sensor import WheelSpeedSensor

WHEEL_SPEEDS = CANMessage(
    arbitration_id=0x0E0,
    name="WHEEL_SPEEDS",
    signals=[
        CANSignal("fl_kph", num_bytes=1, scale=1.0, unit="kph"),
        CANSignal("fr_kph", num_bytes=1, scale=1.0, unit="kph"),
        CANSignal("rl_kph", num_bytes=1, scale=1.0, unit="kph"),
        CANSignal("rr_kph", num_bytes=1, scale=1.0, unit="kph"),
    ],
)

CHASSIS_DYNAMICS = CANMessage(
    arbitration_id=0x0E1,
    name="CHASSIS_DYNAMICS",
    signals=[
        CANSignal("lateral_accel_g", num_bytes=2, scale=0.001, signed=True, unit="g"),
        CANSignal("longitudinal_accel_g", num_bytes=2, scale=0.001, signed=True, unit="g"),
        CANSignal("yaw_rate_deg_s", num_bytes=2, scale=0.1, signed=True, unit="deg/s"),
        CANSignal("steering_angle_deg", num_bytes=2, scale=0.1, signed=True, unit="deg"),
    ],
)

BRAKE_DATA = CANMessage(
    arbitration_id=0x0E2,
    name="BRAKE_DATA",
    signals=[
        CANSignal("brake_pedal_pct", num_bytes=1, scale=1.0, unit="%"),
    ],
)

# A real vehicle-speed reference (for TCS/ABS/ESC slip detection) is
# estimated from the 4 wheel speeds, since an AWD car has no non-driven
# wheel to read directly — the median of the 4 is a simple, real "select"
# technique: robust to any single wheel spinning (fast outlier) or locking
# (slow outlier), since normally at most one wheel is in a slip event at a
# time. Real systems also fuse in accelerometer data to bridge gaps; that
# refinement isn't modeled here.
VEHICLE_REF = CANMessage(
    arbitration_id=0x0E3,
    name="VEHICLE_REF",
    signals=[
        CANSignal("reference_speed_kph", num_bytes=1, scale=1.0, unit="kph"),
    ],
)


class ChassisECU(ECU):
    def __init__(self, bus, body, wheels, steering, brakes):
        super().__init__(bus, "ChassisECU")
        self.body = body
        self.wheels = wheels
        self.steering = steering
        self.brakes = brakes
        self._wheel_speed_sensors = {corner: WheelSpeedSensor(sample_period_s=0.010) for corner in wheels}
        self._last_sensed_kph = {f"{corner}_kph": 0.0 for corner in wheels}

        self.register_message(WHEEL_SPEEDS, period_s=0.010, value_provider=self._wheel_speeds)
        self.register_message(CHASSIS_DYNAMICS, period_s=0.010, value_provider=self._dynamics)
        self.register_message(BRAKE_DATA, period_s=0.020, value_provider=self._brakes)
        self.register_message(VEHICLE_REF, period_s=0.010, value_provider=self._reference_speed)

    def _wheel_speeds(self):
        radius = chassis_specs.TIRE_ROLLING_RADIUS_M
        for corner, wheel in self.wheels.items():
            # A real reluctor-ring wheel speed sensor counts pulses only — it
            # can't tell rotation direction from the pulse train alone (that's
            # a genuine, well-known limitation of this sensor type), so it
            # always reports a magnitude. Direction (forward/reverse) comes
            # from the gear selector elsewhere, not from this sensor.
            sensed_omega = self._wheel_speed_sensors[corner].sense_omega_rad_s(abs(wheel.omega))
            self._last_sensed_kph[f"{corner}_kph"] = sensed_omega * radius * 3.6
        return dict(self._last_sensed_kph)

    def _dynamics(self):
        return {
            "lateral_accel_g": self.body.ay_mps2 / chassis_specs.GRAVITY_MS2,
            "longitudinal_accel_g": self.body.ax_mps2 / chassis_specs.GRAVITY_MS2,
            "yaw_rate_deg_s": math.degrees(self.body.yaw_rate_rad_s),
            "steering_angle_deg": self.steering.wheel_angle_deg,
        }

    def _brakes(self):
        return {"brake_pedal_pct": self.brakes.pedal * 100.0}

    def _reference_speed(self):
        return {"reference_speed_kph": statistics.median(self._last_sensed_kph.values())}
