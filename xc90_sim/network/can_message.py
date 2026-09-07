"""
Byte-packed CAN signal/message definitions.

Real Volvo DBC files (the signal layout an actual XC90's CAN bus uses) are
proprietary and unpublished, so every arbitration ID and signal here is our
own invented layout — plausible in structure (matches how a real
engine/transmission/chassis message set is organized), not a match for any
real vehicle's bus traffic.

Signals here are byte-aligned (not bit-packed within a byte) for simplicity
— a real DBC often packs multiple sub-byte signals into one byte, which this
skips. What's kept: physical-value <-> raw-byte scale/offset conversion,
which is the actual educational core of a CAN signal.
"""

import struct


class CANSignal:
    def __init__(self, name, num_bytes, scale, offset=0.0, signed=False, unit=""):
        self.name = name
        self.num_bytes = num_bytes
        self.scale = scale
        self.offset = offset
        self.signed = signed
        self.unit = unit

    def _struct_format(self):
        sizes = {1: "b", 2: "h", 4: "i"}
        code = sizes[self.num_bytes]
        return ">" + (code if self.signed else code.upper())

    def encode(self, physical_value):
        raw = round((physical_value - self.offset) / self.scale)
        max_raw = 2 ** (8 * self.num_bytes - (1 if self.signed else 0)) - 1
        min_raw = -(2 ** (8 * self.num_bytes - 1)) if self.signed else 0
        raw = max(min_raw, min(max_raw, raw))
        return struct.pack(self._struct_format(), raw)

    def decode(self, raw_bytes):
        raw = struct.unpack(self._struct_format(), raw_bytes)[0]
        return raw * self.scale + self.offset


class CANMessage:
    """A CAN message: an arbitration ID plus an ordered list of byte-aligned signals."""

    def __init__(self, arbitration_id, name, signals):
        self.arbitration_id = arbitration_id
        self.name = name
        self.signals = signals
        self.dlc = sum(s.num_bytes for s in signals)

    def encode(self, values):
        payload = b""
        for signal in self.signals:
            payload += signal.encode(values[signal.name])
        return payload

    def decode(self, payload):
        values = {}
        offset = 0
        for signal in self.signals:
            chunk = payload[offset:offset + signal.num_bytes]
            values[signal.name] = signal.decode(chunk)
            offset += signal.num_bytes
        return values


class CANFrame:
    __slots__ = ("arbitration_id", "data", "message", "period_s")

    def __init__(self, arbitration_id, data, message=None, period_s=None):
        self.arbitration_id = arbitration_id
        self.data = data
        self.message = message  # CANMessage, for convenient decode() by subscribers
        self.period_s = period_s  # transmission period, for time-weighting by consumers
