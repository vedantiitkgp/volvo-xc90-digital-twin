"""
Lighting circuits: headlights, turn indicators (with real blink timing, not
just an on/off flag), hazards, DRLs (Daytime Running Lights), fog lights,
and the interior dome light. Brake lights and reverse lights are real, but
deliberately not settable directly here — they're derived state Simulation
sets each tick from the actual brake pedal / gear selector (same
"compose at the Simulation level, don't couple this class to the rest of
the car" pattern as active_park_zone()/drl_on()), and the dome light is
similarly a mix of a manual override plus real door-open state Simulation
composes in.

DRLs default on whenever the engine is running (see xc90_sim.body.Ignition)
and the headlights aren't manually switched to low/high beam — drl_on()
takes engine_running as a parameter rather than reading Ignition directly,
so this class stays standalone/testable like the rest of xc90_sim.body.
"""

from ..specs import body as specs

HEADLIGHT_MODES = ("off", "parking", "low_beam", "high_beam")


class Lighting:
    def __init__(self):
        self.headlight_mode = "off"
        self.hazards_on = False
        self.fog_lights_on = False
        self.indicator = None  # None, "left", or "right"
        self._blink_on = False
        self._blink_elapsed_s = 0.0
        # Derived/composed state — see module docstring.
        self.brake_lights_on = False
        self.reverse_lights_on = False
        self.dome_light_override = False
        self.dome_light_on = False

    def set_headlight_mode(self, mode):
        if mode not in HEADLIGHT_MODES:
            raise ValueError(f"unknown headlight mode: {mode!r}, expected one of {HEADLIGHT_MODES}")
        self.headlight_mode = mode

    def set_indicator(self, side):
        """side: None (cancel), 'left', or 'right'."""
        self.indicator = side

    def set_hazards(self, on):
        self.hazards_on = on

    def set_fog_lights(self, on):
        self.fog_lights_on = on

    def set_dome_light_override(self, on):
        self.dome_light_override = on

    def drl_on(self, engine_running):
        return engine_running and self.headlight_mode == "off"

    def step(self, dt):
        active = self.hazards_on or self.indicator is not None
        if not active:
            self._blink_on = False
            self._blink_elapsed_s = 0.0
            return

        self._blink_elapsed_s += dt
        half_period_s = 0.5 / specs.INDICATOR_BLINK_HZ
        if self._blink_elapsed_s >= half_period_s:
            self._blink_elapsed_s -= half_period_s
            self._blink_on = not self._blink_on

    def left_indicator_lit(self):
        if self.hazards_on:
            return self._blink_on
        return self._blink_on and self.indicator == "left"

    def right_indicator_lit(self):
        if self.hazards_on:
            return self._blink_on
        return self._blink_on and self.indicator == "right"
