"""
HVAC (climate control) — a genuine first-order thermal model, not just a
setpoint display: cabin temperature evolves each tick from heat exchange
with the outside ambient temperature, an optional solar load, and the
HVAC system's own heating/cooling output (capped by capacity and scaled by
fan speed), the same lumped-thermal-mass technique used for e.g. a house's
HVAC model.

heating_available_frac (see step()) connects this to the real engine
coolant temperature (xc90_sim.cooling.CoolingSystem — a real car's
heater core draws its heat from engine coolant, not a separate electric
element) — a cold engine genuinely can't provide much cabin heat yet, the
classic real-world "car heater takes a few minutes" experience. Cooling
(AC) doesn't depend on this, only heating does.
"""

from ..specs import cabin as specs


class HVAC:
    def __init__(self, initial_cabin_temp_c=20.0):
        self.cabin_temp_c = initial_cabin_temp_c
        self.target_temp_c = 22.0
        self.fan_speed = 3  # 0 (off) - MAX_FAN_SPEED
        self.power_on = True
        self.ac_enabled = True  # if False, can heat but never actively cools
        self.auto_mode = True

    def set_power(self, on):
        self.power_on = on

    def set_target_temp_c(self, temp_c):
        self.target_temp_c = max(specs.MIN_TARGET_TEMP_C, min(specs.MAX_TARGET_TEMP_C, temp_c))

    def set_fan_speed(self, level):
        self.fan_speed = max(0, min(specs.MAX_FAN_SPEED, level))

    def set_ac_enabled(self, enabled):
        self.ac_enabled = enabled

    def step(self, dt, outside_temp_c, solar_load_w=0.0, heating_available_frac=1.0):
        thermal_mass_j_per_k = specs.CABIN_THERMAL_MASS_KJ_PER_K * 1000.0
        passive_w = specs.CABIN_AMBIENT_UA_W_PER_K * (outside_temp_c - self.cabin_temp_c) + solar_load_w

        hvac_w = 0.0
        if self.power_on and self.fan_speed > 0:
            fan_frac = self.fan_speed / specs.MAX_FAN_SPEED
            error = self.target_temp_c - self.cabin_temp_c
            if error > 0.1:
                hvac_w = fan_frac * specs.HVAC_MAX_HEATING_W * heating_available_frac
            elif error < -0.1 and self.ac_enabled:
                hvac_w = -fan_frac * specs.HVAC_MAX_COOLING_W

        self.cabin_temp_c += (passive_w + hvac_w) * dt / thermal_mass_j_per_k
