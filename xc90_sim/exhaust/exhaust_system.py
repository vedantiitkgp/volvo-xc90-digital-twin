"""
Exhaust system: catalytic converter temperature genuinely heats up from
exhaust flow once the engine's running (real cold-start emissions
behavior — a cold catalyst doesn't convert pollutants effectively until
it reaches light-off temperature), and real exhaust backpressure feeds
back into the cylinder's exhaust-stroke pumping loss (see
Cylinder._regime()'s exhaust-pressure handling in cylinder.py, wired via
Engine).
"""

from ..specs import exhaust as specs


class ExhaustSystem:
    def __init__(self, initial_catalyst_temp_c=specs.AMBIENT_TEMP_C):
        self.catalyst_temp_c = initial_catalyst_temp_c

    def step(self, dt, engine_running):
        target_c = specs.EXHAUST_GAS_TEMP_C if engine_running else specs.AMBIENT_TEMP_C
        alpha = dt / (specs.CATALYST_HEATUP_TAU_S + dt)
        self.catalyst_temp_c += alpha * (target_c - self.catalyst_temp_c)

    def catalyst_active(self):
        return self.catalyst_temp_c >= specs.CATALYST_LIGHT_OFF_TEMP_C

    def backpressure_pa(self):
        return specs.BACKPRESSURE_PA
