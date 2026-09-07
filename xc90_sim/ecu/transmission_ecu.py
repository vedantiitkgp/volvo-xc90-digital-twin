"""Transmission control module: broadcasts gear, converter lock state, mode, input shaft speed."""

import numpy as np

from ..network import CANMessage, CANSignal
from .base import ECU

TRANS_DATA = CANMessage(
    arbitration_id=0x0D0,
    name="TRANS_DATA",
    signals=[
        CANSignal("gear", num_bytes=1, scale=1.0),
        CANSignal("converter_locked", num_bytes=1, scale=1.0),
        CANSignal("manual_mode", num_bytes=1, scale=1.0),
        CANSignal("input_shaft_rpm", num_bytes=2, scale=1.0, unit="rpm"),
    ],
)


class TransmissionECU(ECU):
    def __init__(self, bus, transmission, converter, wheels):
        super().__init__(bus, "TransmissionECU")
        self.transmission = transmission
        self.converter = converter
        self.wheels = wheels
        self.register_message(TRANS_DATA, period_s=0.020, value_provider=self._values)  # 50 Hz

    def _values(self):
        # Front differential carrier speed = average of its two output
        # speeds (exact, for an ideal open diff) — what the driveline
        # upstream of the diff actually sees.
        carrier_omega = (self.wheels["fl"].omega + self.wheels["fr"].omega) / 2.0
        input_omega = self.transmission.input_omega(carrier_omega)
        input_rpm = input_omega * 60.0 / (2.0 * np.pi)
        return {
            "gear": self.transmission.gear,
            "converter_locked": 1 if self.converter.locked else 0,
            "manual_mode": 1 if self.transmission.mode == "manual" else 0,
            "input_shaft_rpm": input_rpm,
        }
