"""
Traction control: cuts engine torque when a driven wheel's slip exceeds a
threshold during acceleration. Senses over the CAN bus (WHEEL_SPEEDS,
VEHICLE_REF) — same as a real TCS module, which reads its inputs from other
modules' broadcasts rather than having its own wheel-speed sensor wiring.
Actuates via a direct call to Engine.set_traction_control_limit(); a real
system requests this over CAN too (a torque-reduction request to the ECM),
simplified here to a direct call since round-tripping the actuation over the
bus wouldn't add meaningfully more realism for the complexity it costs.
"""

from ..specs import dsc as specs
from ..ecu.chassis_ecu import WHEEL_SPEEDS, VEHICLE_REF

_DRIVEN_CORNERS = ("fl", "fr", "rl", "rr")  # AWD: all four


class TractionControl:
    def __init__(self, bus):
        self.enabled = True
        self._wheel_kph = {}
        self._reference_kph = 0.0
        bus.subscribe(WHEEL_SPEEDS.arbitration_id, self._on_wheel_speeds)
        bus.subscribe(VEHICLE_REF.arbitration_id, self._on_reference)

    def _on_wheel_speeds(self, frame):
        self._wheel_kph = frame.message.decode(frame.data)

    def _on_reference(self, frame):
        self._reference_kph = frame.message.decode(frame.data)["reference_speed_kph"]

    def set_enabled(self, enabled):
        """Some cars let the driver disable TCS (e.g. a sport/off mode)."""
        self.enabled = enabled

    def torque_limit_frac(self):
        if not self.enabled:
            return 1.0

        ref = max(self._reference_kph, specs.TCS_MIN_REFERENCE_KPH)
        slips = [
            (self._wheel_kph.get(f"{corner}_kph", ref) - ref) / ref
            for corner in _DRIVEN_CORNERS
        ]
        max_slip = max(slips) if slips else 0.0
        if max_slip <= specs.TCS_SLIP_THRESHOLD:
            return 1.0

        cut = specs.TCS_TORQUE_CUT_GAIN * (max_slip - specs.TCS_SLIP_THRESHOLD)
        return max(specs.TCS_MIN_TORQUE_FRACTION, 1.0 - cut)

    def is_active(self):
        """True if TCS is currently cutting engine torque — used by cruise
        control to cancel itself, same as a real car."""
        return self.enabled and self.torque_limit_frac() < 1.0
