"""
ABS: releases/reapplies brake torque per wheel to prevent lockup under
braking. Senses over the CAN bus (WHEEL_SPEEDS, VEHICLE_REF), same as
TractionControl. This is a simplified threshold/hysteresis model of the
real pump-and-valve pressure modulation (which physically pulses at ~15 Hz)
— it captures "don't stay locked, release and reapply" without simulating
the hydraulic valve dynamics themselves.
"""

from ..specs import dsc as specs
from ..ecu.chassis_ecu import WHEEL_SPEEDS, VEHICLE_REF

_CORNERS = ("fl", "fr", "rl", "rr")


class ABS:
    def __init__(self, bus):
        self._wheel_kph = {}
        self._reference_kph = 0.0
        self._releasing = {corner: False for corner in _CORNERS}
        bus.subscribe(WHEEL_SPEEDS.arbitration_id, self._on_wheel_speeds)
        bus.subscribe(VEHICLE_REF.arbitration_id, self._on_reference)

    def _on_wheel_speeds(self, frame):
        self._wheel_kph = frame.message.decode(frame.data)

    def _on_reference(self, frame):
        self._reference_kph = frame.message.decode(frame.data)["reference_speed_kph"]

    def brake_multiplier(self, corner):
        """Returns a 0..1 multiplier to apply to this wheel's brake torque."""
        if self._reference_kph < specs.ABS_MIN_SPEED_KPH:
            self._releasing[corner] = False
            return 1.0

        ref = self._reference_kph
        wheel_kph = self._wheel_kph.get(f"{corner}_kph", ref)
        slip = (wheel_kph - ref) / ref  # negative = wheel slower than vehicle (locking)

        if slip < specs.ABS_LOCKUP_SLIP_THRESHOLD:
            self._releasing[corner] = True
        elif slip > specs.ABS_REAPPLY_SLIP_THRESHOLD:
            self._releasing[corner] = False

        return specs.ABS_RELEASE_FRACTION if self._releasing[corner] else 1.0

    def is_active(self):
        """True if ABS is currently releasing brake torque on any wheel — used
        by cruise control to cancel itself, same as a real car."""
        return any(self._releasing.values())
