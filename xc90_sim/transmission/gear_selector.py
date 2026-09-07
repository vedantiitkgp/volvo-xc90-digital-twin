"""
PRND gear selector: Park/Reverse/Neutral/Drive.

Unlike Transmission's own 1-8 forward-gear shifts (which its adaptive/manual
shift logic changes on its own each tick), this position changes ONLY on an
explicit driver request — nothing in this simulation ever moves the selector
by itself. Two real safety interlocks are modeled: a brake-shift interlock
(can't leave Park without the brake pedal pressed) and a speed interlock
(can't select Park or Reverse while still moving at more than a walking
pace) — the same reason a real car's shifter resists these at speed.
"""

POSITIONS = ("P", "R", "N", "D")

# ASSUMPTION: neither interlock's exact threshold is published; plausible
# values matching how these features behave in most modern automatics.
MIN_BRAKE_FRAC_TO_LEAVE_PARK = 0.05
MAX_SPEED_FOR_PARK_OR_REVERSE_MPS = 3.0


class GearSelector:
    def __init__(self):
        self.position = "P"

    def request(self, position, brake_pedal_frac, vehicle_speed_mps):
        """Attempts to move the selector; returns True if honored, False if
        an interlock blocked it (the position is left unchanged either way
        the caller asks for something not currently allowed)."""
        if position not in POSITIONS:
            raise ValueError(f"unknown gear selector position: {position!r}, expected one of {POSITIONS}")
        if position == self.position:
            return True

        if self.position == "P" and brake_pedal_frac < MIN_BRAKE_FRAC_TO_LEAVE_PARK:
            return False

        if position in ("P", "R") and abs(vehicle_speed_mps) > MAX_SPEED_FOR_PARK_OR_REVERSE_MPS:
            return False

        self.position = position
        return True
