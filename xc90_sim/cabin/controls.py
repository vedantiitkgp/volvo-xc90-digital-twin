"""
Steering wheel buttons (cruise control) and pedal travel.

Cruise control here is a real closed-loop feature, not just a state flag:
when engaged, Simulation drives throttle/brake automatically (via
CruiseController below) to hold the set speed instead of the driver's
manual pedal input. Pressing the brake pedal cancels it, same as a real car.

CruiseController is intentionally a separate, self-contained proportional
controller rather than reusing xc90_sim.trip.driver_model.DriverModel
(same shape of problem, same technique) — xc90_sim.trip sits *above*
xc90_sim.sim (trip/runner.py drives a Simulation), so Simulation reaching
back down into trip would invert that layering and create a circular
import. Keeping the cabin domain self-contained avoids that.
"""

from ..specs import cabin as specs


class CruiseController:
    """Proportional throttle/brake controller tracking a target speed — same technique as
    xc90_sim.trip.driver_model.DriverModel, kept separate to avoid a cross-layer dependency."""

    THROTTLE_GAIN_PER_MPS = 0.20
    BRAKE_GAIN_PER_MPS = 0.30
    DEADBAND_MPS = 0.15
    MAX_THROTTLE_RATE_PER_S = 2.0
    MAX_BRAKE_RATE_PER_S = 4.0

    def __init__(self):
        self.throttle = 0.0
        self.brake = 0.0

    def control(self, target_speed_mps, current_speed_mps, dt):
        """Returns (throttle, brake), each 0..1."""
        error = target_speed_mps - current_speed_mps
        if error > self.DEADBAND_MPS:
            throttle_target, brake_target = min(1.0, self.THROTTLE_GAIN_PER_MPS * error), 0.0
        elif error < -self.DEADBAND_MPS:
            throttle_target, brake_target = 0.0, min(1.0, self.BRAKE_GAIN_PER_MPS * -error)
        else:
            throttle_target, brake_target = 0.0, 0.0

        max_throttle_step = self.MAX_THROTTLE_RATE_PER_S * dt
        max_brake_step = self.MAX_BRAKE_RATE_PER_S * dt
        self.throttle += max(-max_throttle_step, min(max_throttle_step, throttle_target - self.throttle))
        self.brake += max(-max_brake_step, min(max_brake_step, brake_target - self.brake))
        return self.throttle, self.brake


class SteeringWheelControls:
    def __init__(self):
        self.cruise_control_engaged = False
        self.cruise_set_speed_kph = None

    def press_cruise_set(self, current_speed_kph):
        self.cruise_control_engaged = True
        self.cruise_set_speed_kph = current_speed_kph

    def press_cruise_resume(self):
        if self.cruise_set_speed_kph is not None:
            self.cruise_control_engaged = True

    def press_cruise_cancel(self):
        self.cruise_control_engaged = False

    def adjust_cruise_speed_kph(self, delta_kph):
        if self.cruise_set_speed_kph is not None:
            self.cruise_set_speed_kph = max(0.0, self.cruise_set_speed_kph + delta_kph)


class PedalInputs:
    """Accelerator/brake 0-100% command -> physical pedal travel (mm) — a telemetry/realism
    layer over the existing 0-1 throttle/brake fractions, not a replacement for them."""

    def __init__(self):
        self.accelerator_pct = 0.0
        self.brake_pct = 0.0

    def set_accelerator_pct(self, pct):
        self.accelerator_pct = max(0.0, min(100.0, pct))

    def set_brake_pct(self, pct):
        self.brake_pct = max(0.0, min(100.0, pct))

    def accelerator_travel_mm(self):
        return self.accelerator_pct / 100.0 * specs.ACCELERATOR_MAX_TRAVEL_MM

    def brake_travel_mm(self):
        return self.brake_pct / 100.0 * specs.BRAKE_MAX_TRAVEL_MM
