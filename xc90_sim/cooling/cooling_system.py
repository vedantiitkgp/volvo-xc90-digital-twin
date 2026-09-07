"""
Cooling system: coolant temperature genuinely evolves from real engine fuel
energy input (a fraction of it -- see specs.cooling's COOLANT_HEAT_
FRACTION_OF_FUEL_ENERGY -- rather than a true instantaneous waste-heat
balance, which would need exact crank output power across every driveline
branch to derive precisely) minus heat rejected through the radiator,
whose effectiveness genuinely depends on airflow (vehicle speed + electric
fan) — not an assumed constant operating temperature. The thermostat
blocks radiator flow while cold (letting the engine warm up faster) and
opens once at temperature.

Feeds HVAC's cabin heating (see Simulation.step()) — a genuinely cold
engine can't provide much cabin heat yet, the classic real-world "car
heater takes a few minutes to warm up" experience.
"""

from ..specs import cooling as specs


class CoolingSystem:
    def __init__(self, initial_coolant_temp_c=20.0):
        self.coolant_temp_c = initial_coolant_temp_c
        self.thermostat_open = False
        self.fan_on = False

    def step(self, dt, fuel_energy_rate_w, vehicle_speed_mps, ambient_temp_c, coolant_flow_frac=1.0):
        """coolant_flow_frac (0..1, default 1.0): real coolant-side flow
        rate from the electric water pump (see WaterPump) -- radiator
        rejection needs BOTH airflow (existing) and coolant flow to move
        heat; low flow (cold start, or a failed pump) starves rejection
        even at full airflow, same as a real car."""
        coolant_heat_w = fuel_energy_rate_w * specs.COOLANT_HEAT_FRACTION_OF_FUEL_ENERGY

        if self.coolant_temp_c >= specs.THERMOSTAT_OPEN_TEMP_C:
            self.thermostat_open = True
        elif self.coolant_temp_c < specs.THERMOSTAT_OPEN_TEMP_C - 3.0:
            self.thermostat_open = False

        if self.coolant_temp_c >= specs.FAN_ON_TEMP_C:
            self.fan_on = True
        elif self.coolant_temp_c < specs.FAN_OFF_TEMP_C:
            self.fan_on = False

        radiator_reject_w = 0.0
        if self.thermostat_open:
            speed_frac = min(1.0, abs(vehicle_speed_mps) / 30.0)  # ram-air effect, saturates ~30 m/s
            airflow_frac = max(speed_frac, specs.RADIATOR_STATIONARY_DISSIPATION_FRAC if self.fan_on else 0.0)
            radiator_reject_w = specs.RADIATOR_MAX_DISSIPATION_W * airflow_frac * coolant_flow_frac

        passive_loss_w = specs.AMBIENT_HEAT_LOSS_W_PER_K * (self.coolant_temp_c - ambient_temp_c)

        net_w = coolant_heat_w - radiator_reject_w - passive_loss_w
        self.coolant_temp_c += net_w * dt / specs.COOLANT_THERMAL_MASS_J_PER_K

    def overheating(self):
        return self.coolant_temp_c >= specs.OVERHEAT_WARNING_TEMP_C

    def heating_available_frac(self):
        """How much cabin heat the heater core can provide right now —
        genuinely gated by real coolant temperature, not always 100%."""
        cold_floor_c = specs.THERMOSTAT_OPEN_TEMP_C - 20.0
        if self.coolant_temp_c <= cold_floor_c:
            return 0.0
        if self.coolant_temp_c >= specs.NORMAL_OPERATING_TEMP_C:
            return 1.0
        return (self.coolant_temp_c - cold_floor_c) / (specs.NORMAL_OPERATING_TEMP_C - cold_floor_c)
