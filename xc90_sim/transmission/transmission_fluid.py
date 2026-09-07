"""
Transmission fluid (ATF): temperature genuinely heated by real torque
converter slip loss (the actual power difference between what the pump
absorbs and what the turbine delivers while unlocked — a real, physical
heat source, not assumed), cooled by a real transmission cooler (see
xc90_sim.transmission.TransmissionCooler — its own airflow-dependent
object, not a bare constant here anymore). condition (from the wear
model) is tracked for maintenance-due purposes, same as the timing/
accessory belts.
"""

# ASSUMPTION: not published for this car; plausible for this class of
# 8-speed automatic's fluid system.
THERMAL_MASS_J_PER_K = 8000.0
OVERHEAT_WARNING_TEMP_C = 120.0


class TransmissionFluid:
    def __init__(self, initial_temp_c=20.0, condition=1.0):
        self.temp_c = initial_temp_c
        self.condition = condition

    def step(self, dt, slip_heat_w, ambient_temp_c, cooler_dissipation_w_per_k):
        cooler_reject_w = cooler_dissipation_w_per_k * (self.temp_c - ambient_temp_c)
        net_w = slip_heat_w - cooler_reject_w
        self.temp_c += net_w * dt / THERMAL_MASS_J_PER_K

    def overheating(self):
        return self.temp_c >= OVERHEAT_WARNING_TEMP_C
