"""
Engine Auto Start/Stop: shuts the engine off at a stop (Drive/Neutral,
brake held, essentially stationary) to save fuel, then restarts
automatically the instant the driver releases the brake or needs to move —
NOT the same as the ignition being off: accessories/ignition stay fully on
throughout, only the engine itself stops turning. Many real cars let the
driver disable this per-trip via a dash button; modeled the same way here.
"""

from ..specs import engine as specs


class AutoStopStart:
    def __init__(self):
        self.enabled = True
        self.engine_auto_stopped = False

    def set_enabled(self, enabled):
        self.enabled = enabled
        if not enabled:
            self.engine_auto_stopped = False  # disabling mid-stop forces an immediate resume

    def step(self, ignition_engine_running, vehicle_speed_mps, brake_pedal_frac, gear_position):
        if not self.enabled or not ignition_engine_running:
            self.engine_auto_stopped = False
            return

        if self.engine_auto_stopped:
            if brake_pedal_frac < specs.AUTO_STOP_RESUME_BRAKE_FRAC or gear_position not in ("D", "N"):
                self.engine_auto_stopped = False
        else:
            if (abs(vehicle_speed_mps) < specs.AUTO_STOP_MAX_SPEED_MPS
                    and brake_pedal_frac >= specs.AUTO_STOP_MIN_BRAKE_FRAC_TO_ENGAGE
                    and gear_position in ("D", "N")):
                self.engine_auto_stopped = True
