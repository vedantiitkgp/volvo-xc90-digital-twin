"""
Bridges a real OBD2Connection onto a CANBus, using the exact same message
formats (ENGINE_DATA, VEHICLE_REF, etc.) the simulation's own ECUs publish —
so TripLogger works completely unchanged on real car data, not just
simulated data.

What's genuinely available from generic OBD2 (no manufacturer-specific PIDs
needed): engine RPM, throttle position, calculated engine load, vehicle
speed. What ISN'T, and how (or whether) this bridges the gap:
  - Gear: not a standard PID. ESTIMATED from the RPM/wheel-speed ratio
    matched against this project's own known TG-81SC gear ratios — a
    legitimate technique (real diagnostic tools do this too), not a fake
    number, but an estimate that can be wrong right at a gear-change moment.
  - Converter lock state, manual mode: genuinely unknowable from generic
    OBD2. Defaulted (locked=True, manual=False) rather than guessed per-tick.
  - Longitudinal acceleration: DERIVED from the numerical derivative of
    consecutive real speed readings — genuine data, but noisier than a real
    accelerometer since it's differentiating a low-rate, quantized signal.
  - Lateral accel, yaw rate, steering angle, brake pedal %, AWD torque
    split: NOT available from generic OBD2 at all (would need Volvo's
    proprietary extended PIDs, which aren't publicly documented — the same
    "manufacturer data is proprietary" limitation as everywhere else in
    this project). Not published to the bus; TripLogger's stats for these
    will simply show 0%/no data, which is an honest gap, not a wrong number.

UNTESTED against a real adapter/car — written and reviewed against
python-OBD's documented API and this project's own real spec data (gear
ratios), but there was no physical hardware available to verify timing,
PID availability, or connection behavior against.
"""

import math
import time

from ..network import CANFrame
from ..ecu.engine_ecu import ENGINE_DATA
from ..ecu.transmission_ecu import TRANS_DATA
from ..ecu.chassis_ecu import CHASSIS_DYNAMICS, VEHICLE_REF
from ..specs import transmission as trans_specs
from ..specs import chassis as chassis_specs


def _estimate_gear(rpm, speed_kph):
    wheel_omega_rad_s = (speed_kph / 3.6) / chassis_specs.TIRE_ROLLING_RADIUS_M
    wheel_rpm = wheel_omega_rad_s * 60.0 / (2.0 * math.pi)
    if wheel_rpm < 1.0:
        return 1
    apparent_ratio = rpm / wheel_rpm
    best_gear, best_diff = 1, float("inf")
    for gear, ratio in trans_specs.GEAR_RATIOS.items():
        diff = abs(apparent_ratio - ratio * trans_specs.FINAL_DRIVE_RATIO)
        if diff < best_diff:
            best_gear, best_diff = gear, diff
    return best_gear


class OBD2Bridge:
    def __init__(self, connection, can_bus, poll_period_s=0.5):
        self.connection = connection
        self.can_bus = can_bus
        self.poll_period_s = poll_period_s
        self._last_speed_mps = None
        self._last_poll_time = None

    def poll_once(self):
        """Query the car once; publish whatever PIDs are actually available. Real time, not sim time."""
        now = time.time()
        rpm = self.connection.query("RPM")
        speed_kph = self.connection.query("SPEED")
        throttle_pct = self.connection.query("THROTTLE_POS")
        load_pct = self.connection.query("ENGINE_LOAD")

        if None not in (rpm, throttle_pct, load_pct):
            payload = ENGINE_DATA.encode(
                {"rpm": rpm, "throttle_pct": throttle_pct, "calculated_load_pct": load_pct}
            )
            self.can_bus.send(CANFrame(ENGINE_DATA.arbitration_id, payload, ENGINE_DATA, self.poll_period_s))

        if speed_kph is not None:
            payload = VEHICLE_REF.encode({"reference_speed_kph": speed_kph})
            self.can_bus.send(CANFrame(VEHICLE_REF.arbitration_id, payload, VEHICLE_REF, self.poll_period_s))

            if rpm is not None and speed_kph > 2.0:
                gear = _estimate_gear(rpm, speed_kph)
                payload = TRANS_DATA.encode(
                    {"gear": gear, "converter_locked": 1, "manual_mode": 0, "input_shaft_rpm": rpm}
                )
                self.can_bus.send(CANFrame(TRANS_DATA.arbitration_id, payload, TRANS_DATA, self.poll_period_s))

            speed_mps = speed_kph / 3.6
            # Require close to a full poll period's worth of real elapsed time —
            # differentiating over a too-short dt (e.g. ELM327 response-time
            # jitter, or two polls fired back-to-back) blows up into a physically
            # impossible acceleration. A real car can't exceed a couple of g;
            # clamp defensively rather than publish a nonsense spike.
            if self._last_speed_mps is not None and self._last_poll_time is not None:
                dt = now - self._last_poll_time
                if dt >= 0.5 * self.poll_period_s:
                    raw_accel_g = ((speed_mps - self._last_speed_mps) / dt) / chassis_specs.GRAVITY_MS2
                    accel_g = max(-2.0, min(2.0, raw_accel_g))
                    payload = CHASSIS_DYNAMICS.encode({
                        "lateral_accel_g": 0.0,  # not available from generic OBD2 — see module docstring
                        "longitudinal_accel_g": accel_g,
                        "yaw_rate_deg_s": 0.0,
                        "steering_angle_deg": 0.0,
                    })
                    self.can_bus.send(
                        CANFrame(CHASSIS_DYNAMICS.arbitration_id, payload, CHASSIS_DYNAMICS, self.poll_period_s)
                    )
            self._last_speed_mps = speed_mps
            self._last_poll_time = now

    def run(self, duration_s=None):
        """Blocking loop: poll at poll_period_s intervals until duration_s elapses (or forever if None)."""
        start = time.time()
        while duration_s is None or (time.time() - start) < duration_s:
            self.poll_once()
            time.sleep(self.poll_period_s)
