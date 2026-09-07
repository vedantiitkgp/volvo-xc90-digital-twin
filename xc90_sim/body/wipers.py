"""
Front and rear windshield wipers: a speed setting plus a real sweep-cycle
timer (not just an on/off flag) — front_sweeping()/rear_sweeping() report
whether a physical wipe is actively happening right now, vs. the pause
between sweeps at "intermittent" speed.
"""

from ..specs import body as specs

FRONT_SPEEDS = ("off", "intermittent", "low", "high")
REAR_SPEEDS = ("off", "intermittent", "on")


class Wipers:
    def __init__(self):
        self.front_speed = "off"
        self.rear_speed = "off"
        self._front_cycle_elapsed_s = 0.0
        self._rear_cycle_elapsed_s = 0.0

    def set_front_speed(self, speed):
        if speed not in FRONT_SPEEDS:
            raise ValueError(f"unknown front wiper speed: {speed!r}, expected one of {FRONT_SPEEDS}")
        self.front_speed = speed
        self._front_cycle_elapsed_s = 0.0

    def set_rear_speed(self, speed):
        if speed not in REAR_SPEEDS:
            raise ValueError(f"unknown rear wiper speed: {speed!r}, expected one of {REAR_SPEEDS}")
        self.rear_speed = speed
        self._rear_cycle_elapsed_s = 0.0

    def step(self, dt):
        if self.front_speed != "off":
            cycle_s = specs.FRONT_WIPER_CYCLE_S[self.front_speed]
            self._front_cycle_elapsed_s = (self._front_cycle_elapsed_s + dt) % cycle_s
        if self.rear_speed != "off":
            cycle_s = specs.REAR_WIPER_CYCLE_S[self.rear_speed]
            self._rear_cycle_elapsed_s = (self._rear_cycle_elapsed_s + dt) % cycle_s

    def front_sweeping(self):
        return self.front_speed != "off" and self._front_cycle_elapsed_s < specs.WIPER_SWEEP_DURATION_S

    def rear_sweeping(self):
        return self.rear_speed != "off" and self._rear_cycle_elapsed_s < specs.WIPER_SWEEP_DURATION_S
