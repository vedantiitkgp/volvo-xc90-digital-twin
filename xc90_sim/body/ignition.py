"""
Volvo's distinctive rotary Start/Stop knob: OFF -> (turn to crank) -> RUN,
push to return to OFF. ACCESSORY (infotainment/HVAC available, engine off)
is a real intermediate state some cars reach via a partial turn -- modeled
here as directly reachable via to_accessory(), not as a detent on the same
rotation as start.

A real brake-to-start interlock is modeled too: turning the knob to crank
does nothing without the brake pedal pressed, same as push-button start on
most modern cars.
"""

from ..specs import engine as specs

STATES = ("off", "accessory", "cranking", "run")


class Ignition:
    def __init__(self):
        self.state = "off"
        self._cranking_elapsed_s = 0.0

    def to_accessory(self):
        if self.state == "off":
            self.state = "accessory"

    def rotate_to_start(self, brake_pedal_frac):
        """Returns True if the knob turn was honored, False if the brake-to-start interlock blocked it."""
        if brake_pedal_frac < specs.MIN_BRAKE_FRAC_TO_START:
            return False
        if self.state in ("off", "accessory"):
            self.state = "cranking"
            self._cranking_elapsed_s = 0.0
        return True

    def push_to_stop(self):
        self.state = "off"
        self._cranking_elapsed_s = 0.0

    def step(self, dt):
        if self.state == "cranking":
            self._cranking_elapsed_s += dt
            if self._cranking_elapsed_s >= specs.STARTER_CRANK_TIME_S:
                self.state = "run"

    @property
    def engine_running(self):
        return self.state == "run"

    @property
    def accessory_power(self):
        return self.state in ("accessory", "run")
