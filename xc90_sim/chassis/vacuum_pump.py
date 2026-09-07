"""
Electric brake-booster vacuum pump. Real, specific reason this exists on
this engine rather than a mechanical cam/belt-driven pump: independent
variable valve timing on both camshafts leaves too little manifold vacuum
at low rpm for the brake booster, so this car uses a small electric pump
switched on by a vacuum switch when the reservoir runs low, off once
restored — real hysteresis behavior, not a continuously-running pump
(these aren't rated to run continuously). Draws real electrical power
while active. See specs/chassis.py for sourcing/ASSUMPTION notes.
"""

from ..specs import chassis as specs
from ..specs import accessories as acc_specs


class VacuumPump:
    def __init__(self):
        self.reservoir_vacuum_kpa = specs.VACUUM_RESERVOIR_FULL_KPA
        self.running = False

    def step(self, dt, brake_pedal_frac):
        consumption_kpa = specs.VACUUM_CONSUMPTION_KPA_PER_S * brake_pedal_frac * dt
        self.reservoir_vacuum_kpa = max(0.0, self.reservoir_vacuum_kpa - consumption_kpa)

        if self.reservoir_vacuum_kpa <= specs.VACUUM_PUMP_ON_KPA:
            self.running = True
        elif self.reservoir_vacuum_kpa >= specs.VACUUM_PUMP_OFF_KPA:
            self.running = False

        if self.running:
            self.reservoir_vacuum_kpa = min(
                specs.VACUUM_RESERVOIR_FULL_KPA,
                self.reservoir_vacuum_kpa + specs.VACUUM_PUMP_BUILD_KPA_PER_S * dt,
            )

    def electrical_load_w(self):
        return acc_specs.VACUUM_PUMP_ELECTRICAL_W if self.running else 0.0
