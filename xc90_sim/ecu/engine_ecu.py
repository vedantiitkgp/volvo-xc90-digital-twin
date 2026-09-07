"""Engine control module: broadcasts RPM, throttle, calculated load, and MAP (manifold pressure)."""

import random

from ..network import CANMessage, CANSignal
from .base import ECU

# A real MAP sensor (standard OBD2 PID 0x0B, "Intake Manifold Absolute
# Pressure") has genuine measurement noise, same reasoning as
# WheelSpeedSensor's pulse-quantization treatment for wheel speed --
# real sensors aren't perfect, even when the underlying physics (see
# Engine.manifold_pressure_pa, now a genuine combustion-model quantity
# rather than an assumed constant) is.
MAP_SENSOR_NOISE_STD_KPA = 1.5  # ASSUMPTION: plausible for this class of sensor

ENGINE_DATA = CANMessage(
    arbitration_id=0x0C0,
    name="ENGINE_DATA",
    signals=[
        CANSignal("rpm", num_bytes=2, scale=1.0, unit="rpm"),
        CANSignal("throttle_pct", num_bytes=1, scale=1.0, unit="%"),
        CANSignal("calculated_load_pct", num_bytes=1, scale=1.0, unit="%"),
        CANSignal("map_kpa", num_bytes=1, scale=1.0, unit="kPa"),
    ],
)


class EngineECU(ECU):
    def __init__(self, bus, engine):
        super().__init__(bus, "EngineECU")
        self.engine = engine
        self.register_message(ENGINE_DATA, period_s=0.010, value_provider=self._values)  # 100 Hz

    def _values(self):
        sensed_map_kpa = self.engine.manifold_pressure_pa / 1000.0 + random.gauss(0.0, MAP_SENSOR_NOISE_STD_KPA)
        return {
            "rpm": self.engine.rpm,
            "throttle_pct": self.engine.throttle * 100.0,
            "calculated_load_pct": self.engine.calculated_load_frac * 100.0,
            "map_kpa": max(0.0, sensed_map_kpa),
        }
