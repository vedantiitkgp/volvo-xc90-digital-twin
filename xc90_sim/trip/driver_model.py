"""Simple proportional driver: tracks a target speed with throttle or brake, never both."""


class DriverModel:
    # ASSUMPTION: proportional gains tuned for reasonably prompt but non-jerky tracking.
    THROTTLE_GAIN_PER_MPS = 0.20
    BRAKE_GAIN_PER_MPS = 0.30
    DEADBAND_MPS = 0.15

    # A real driver eases into the pedal rather than instantly flooring it —
    # without this, every stop-light launch in a drive cycle looks like a
    # full-throttle drag-strip start, which skews the usage stats.
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
