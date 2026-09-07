"""Haldex AWD control module: broadcasts current front/rear torque bias."""

from ..network import CANMessage, CANSignal
from .base import ECU

AWD_DATA = CANMessage(
    arbitration_id=0x0F0,
    name="AWD_DATA",
    signals=[
        CANSignal("front_bias_pct", num_bytes=1, scale=1.0, unit="%"),
    ],
)


class AWDECU(ECU):
    def __init__(self, bus, awd):
        super().__init__(bus, "AWDECU")
        self.awd = awd
        self.register_message(AWD_DATA, period_s=0.050, value_provider=self._values)  # 20 Hz

    def _values(self):
        return {"front_bias_pct": self.awd.front_bias * 100.0}
