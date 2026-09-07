"""Aisin TG-81SC 8-speed automatic (see specs/transmission.py for the naming correction): gear ratios, adaptive auto-shift logic, and Geartronic manual mode."""

import numpy as np

from ..specs import transmission as specs
from ..specs import engine as engine_specs


def _shift_up_rpm(throttle):
    # ASSUMPTION: adaptive shift map — shifts early at light throttle for
    # economy, holds gears near redline under full throttle.
    return float(np.interp(throttle, [0.0, 0.3, 1.0], [1800, 2800, 6000]))


def _shift_down_rpm(throttle):
    return float(np.interp(throttle, [0.0, 0.3, 1.0], [900, 1100, 2200]))


class Transmission:
    """
    Models the TG-81SC in two modes:
      - 'auto' (default): adaptive shift points based on throttle position.
      - 'manual' (Geartronic tip-shift): gear only changes on an explicit
        request_upshift()/request_downshift() call.
    Over-rev and stall protection (auto shift near redline/idle) applies in
    both modes, matching real Geartronic behavior.
    """

    def __init__(self):
        self.gear = 1
        self.mode = "auto"
        self._shift_cooldown_s = 0.0
        self._pending_manual_shift = 0  # +1 upshift, -1 downshift, 0 none queued

    @property
    def ratio(self):
        return specs.GEAR_RATIOS[self.gear] * specs.FINAL_DRIVE_RATIO

    def output_torque_nm(self, input_torque_nm):
        """Torque at the transmission output shaft, before drive losses."""
        return input_torque_nm * self.ratio

    def input_omega(self, output_omega):
        """Transmission input-shaft speed (rad/s) implied by output speed."""
        return output_omega * self.ratio

    def set_mode(self, mode):
        if mode not in ("auto", "manual"):
            raise ValueError(f"unknown transmission mode: {mode!r}")
        self.mode = mode

    def request_upshift(self):
        """Queue a Geartronic tip-shift upshift for the next step() call."""
        self._pending_manual_shift = 1

    def request_downshift(self):
        self._pending_manual_shift = -1

    def step(self, dt, input_rpm, throttle):
        """Run shift logic; mutates self.gear. Call once per sim tick."""
        self._shift_cooldown_s = max(0.0, self._shift_cooldown_s - dt)
        manual_shift, self._pending_manual_shift = self._pending_manual_shift, 0
        if self._shift_cooldown_s > 0.0:
            return

        max_gear = max(specs.GEAR_RATIOS)

        # Over-rev / stall protection, active regardless of mode.
        if input_rpm > engine_specs.REDLINE_RPM - 100 and self.gear < max_gear:
            self.gear += 1
            self._shift_cooldown_s = 0.4  # ASSUMPTION: shift settle time
            return
        if input_rpm < engine_specs.IDLE_RPM + 100 and self.gear > 1:
            self.gear -= 1
            self._shift_cooldown_s = 0.4
            return

        if self.mode == "manual":
            if manual_shift == 1 and self.gear < max_gear:
                self.gear += 1
                self._shift_cooldown_s = 0.4
            elif manual_shift == -1 and self.gear > 1:
                self.gear -= 1
                self._shift_cooldown_s = 0.4
            return

        if input_rpm > _shift_up_rpm(throttle) and self.gear < max_gear:
            self.gear += 1
            self._shift_cooldown_s = 0.4
        elif input_rpm < _shift_down_rpm(throttle) and self.gear > 1:
            self.gear -= 1
            self._shift_cooldown_s = 0.4
