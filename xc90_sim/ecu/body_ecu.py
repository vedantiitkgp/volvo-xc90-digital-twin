"""Body control module ECU: doors/hood/tailgate/lock, windows, mirrors, lighting, wipers, and sunroof."""

from ..network import CANMessage, CANSignal
from .base import ECU

BODY_STATUS = CANMessage(
    arbitration_id=0x1A0,
    name="BODY_STATUS",
    signals=[
        CANSignal("door_fl_open", num_bytes=1, scale=1.0),
        CANSignal("door_fr_open", num_bytes=1, scale=1.0),
        CANSignal("door_rl_open", num_bytes=1, scale=1.0),
        CANSignal("door_rr_open", num_bytes=1, scale=1.0),
        CANSignal("hood_open", num_bytes=1, scale=1.0),
        CANSignal("tailgate_open", num_bytes=1, scale=1.0),
        CANSignal("locked", num_bytes=1, scale=1.0),
        CANSignal("ajar_warning", num_bytes=1, scale=1.0),
    ],
)

WINDOW_STATUS = CANMessage(
    arbitration_id=0x1A1,
    name="WINDOW_STATUS",
    signals=[
        CANSignal("fl_pct", num_bytes=1, scale=1.0, unit="%"),
        CANSignal("fr_pct", num_bytes=1, scale=1.0, unit="%"),
        CANSignal("rl_pct", num_bytes=1, scale=1.0, unit="%"),
        CANSignal("rr_pct", num_bytes=1, scale=1.0, unit="%"),
    ],
)

_HEADLIGHT_MODE_CODES = {"off": 0, "parking": 1, "low_beam": 2, "high_beam": 3}

LIGHTING_STATUS = CANMessage(
    arbitration_id=0x1A2,
    name="LIGHTING_STATUS",
    signals=[
        CANSignal("headlight_mode", num_bytes=1, scale=1.0),
        CANSignal("left_indicator_lit", num_bytes=1, scale=1.0),
        CANSignal("right_indicator_lit", num_bytes=1, scale=1.0),
        CANSignal("hazards_on", num_bytes=1, scale=1.0),
        CANSignal("mirrors_folded", num_bytes=1, scale=1.0),
    ],
)

WIPER_STATUS = CANMessage(
    arbitration_id=0x1A3,
    name="WIPER_STATUS",
    signals=[
        CANSignal("front_speed", num_bytes=1, scale=1.0),
        CANSignal("rear_speed", num_bytes=1, scale=1.0),
        CANSignal("front_sweeping", num_bytes=1, scale=1.0),
        CANSignal("rear_sweeping", num_bytes=1, scale=1.0),
    ],
)

_WIPER_FRONT_SPEED_CODES = {"off": 0, "intermittent": 1, "low": 2, "high": 3}
_WIPER_REAR_SPEED_CODES = {"off": 0, "intermittent": 1, "on": 2}
_SUNROOF_GLASS_STATE_CODES = {"closed": 0, "vent": 1, "open": 2}

SUNROOF_STATUS = CANMessage(
    arbitration_id=0x1A4,
    name="SUNROOF_STATUS",
    signals=[
        CANSignal("glass_state", num_bytes=1, scale=1.0),
        CANSignal("shade_open", num_bytes=1, scale=1.0),
    ],
)


class BodyECU(ECU):
    def __init__(self, bus, closures, windows, mirrors, lighting, wipers, sunroof):
        super().__init__(bus, "BodyECU")
        self.closures = closures
        self.windows = windows
        self.mirrors = mirrors
        self.lighting = lighting
        self.wipers = wipers
        self.sunroof = sunroof
        self.register_message(BODY_STATUS, period_s=0.1, value_provider=self._closure_values)  # 10 Hz
        self.register_message(WINDOW_STATUS, period_s=0.1, value_provider=self._window_values)
        self.register_message(LIGHTING_STATUS, period_s=0.05, value_provider=self._lighting_values)  # 20 Hz
        self.register_message(WIPER_STATUS, period_s=0.05, value_provider=self._wiper_values)  # 20 Hz
        self.register_message(SUNROOF_STATUS, period_s=0.2, value_provider=self._sunroof_values)  # 5 Hz

    def _closure_values(self):
        c = self.closures
        return {
            "door_fl_open": 1 if c.door_open["fl"] else 0,
            "door_fr_open": 1 if c.door_open["fr"] else 0,
            "door_rl_open": 1 if c.door_open["rl"] else 0,
            "door_rr_open": 1 if c.door_open["rr"] else 0,
            "hood_open": 1 if c.hood_open else 0,
            "tailgate_open": 1 if c.tailgate_open else 0,
            "locked": 1 if c.locked else 0,
            "ajar_warning": 1 if c.ajar_warning() else 0,
        }

    def _window_values(self):
        p = self.windows.position_pct
        return {"fl_pct": p["fl"], "fr_pct": p["fr"], "rl_pct": p["rl"], "rr_pct": p["rr"]}

    def _lighting_values(self):
        light = self.lighting
        return {
            "headlight_mode": _HEADLIGHT_MODE_CODES[light.headlight_mode],
            "left_indicator_lit": 1 if light.left_indicator_lit() else 0,
            "right_indicator_lit": 1 if light.right_indicator_lit() else 0,
            "hazards_on": 1 if light.hazards_on else 0,
            "mirrors_folded": 1 if self.mirrors.folded else 0,
        }

    def _wiper_values(self):
        w = self.wipers
        return {
            "front_speed": _WIPER_FRONT_SPEED_CODES[w.front_speed],
            "rear_speed": _WIPER_REAR_SPEED_CODES[w.rear_speed],
            "front_sweeping": 1 if w.front_sweeping() else 0,
            "rear_sweeping": 1 if w.rear_sweeping() else 0,
        }

    def _sunroof_values(self):
        return {
            "glass_state": _SUNROOF_GLASS_STATE_CODES[self.sunroof.glass_state],
            "shade_open": 1 if self.sunroof.shade_open else 0,
        }
