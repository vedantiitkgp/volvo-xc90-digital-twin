"""Hydraulic torque converter with lockup clutch."""

import numpy as np

from ..specs import transmission as specs


class TorqueConverter:
    """
    Couples engine (pump side) to transmission input shaft (turbine side),
    using the standard two-curve converter model:

      pump_torque   = capacity_factor(SR) * pump_omega^2      (hydraulic load
                       the engine feels, independent of engine fueling)
      turbine_torque = pump_torque * torque_ratio(SR)          (multiplication)

    Above the lockup speed ratio the clutch is modeled as a direct 1:1,
    slip-free connection instead.

    The lockup decision and the fluid-coupling physics deliberately use two
    different turbine-speed signals (see Simulation.step): the physical
    capacity/multiplier curves use the real, slip-including turbine speed
    (that's genuinely what the fluid inside the converter sees), but the
    lockup *solenoid decision* uses an idealized vehicle-speed-derived
    turbine speed — real TCUs don't rigidly lock the engine to a wheel that's
    spinning freely, so the control decision needs a slip-immune signal.
    """

    def __init__(self):
        self.locked = False
        self.physical_speed_ratio = 0.0

    def speed_ratio_of(self, pump_omega, turbine_omega):
        if pump_omega < 1e-3:
            return 0.0
        return float(np.clip(turbine_omega / pump_omega, 0.0, 1.0))

    def pump_load_torque_nm(self, pump_omega):
        """Hydraulic resistive torque the pump presents to the engine (unlocked only)."""
        return specs.CONVERTER_CAPACITY_FACTOR * pump_omega * pump_omega

    def turbine_torque_nm(self, pump_torque_nm):
        multiplier = float(np.interp(
            self.physical_speed_ratio, specs.CONVERTER_SPEED_RATIO, specs.CONVERTER_TORQUE_MULTIPLIER
        ))
        return pump_torque_nm * multiplier

    def update(self, pump_omega, physical_turbine_omega, control_turbine_omega):
        """Update physical SR (fluid coupling) and the lockup decision (control signal)."""
        self.physical_speed_ratio = self.speed_ratio_of(pump_omega, physical_turbine_omega)
        control_speed_ratio = self.speed_ratio_of(pump_omega, control_turbine_omega)
        self.locked = control_speed_ratio >= specs.CONVERTER_LOCKUP_SPEED_RATIO
        return self.locked
