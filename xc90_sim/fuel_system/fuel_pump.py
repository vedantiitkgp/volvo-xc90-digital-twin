"""
Fuel pump: electric in-tank lift pump feeding a camshaft-driven high-
pressure pump (this is a direct-injection engine, so real fuel rail
pressure is genuinely high, ~150 bar). Pressure builds over real time
after the ignition calls for it (not instant) and bleeds down when off.
Low pressure derates achievable injector flow — see FuelInjector — the
same real coupling a GDI system has. The lift pump itself is also a real
electrical load on the alternator (see electrical_load_w()).
"""

from ..specs import accessories as specs


class FuelPump:
    def __init__(self):
        self.pressure_bar = 0.0
        self.running = False

    def set_running(self, running):
        self.running = running

    def step(self, dt):
        target_bar = specs.HIGH_PRESSURE_TARGET_BAR if self.running else 0.0
        rate_bar_per_s = specs.HIGH_PRESSURE_TARGET_BAR / specs.PRESSURE_BUILD_TIME_S
        max_step_bar = rate_bar_per_s * dt
        delta = max(-max_step_bar, min(max_step_bar, target_bar - self.pressure_bar))
        self.pressure_bar = max(0.0, self.pressure_bar + delta)

    @property
    def pressure_fraction(self):
        return self.pressure_bar / specs.HIGH_PRESSURE_TARGET_BAR

    def electrical_load_w(self):
        return specs.FUEL_PUMP_ELECTRICAL_W if self.running else 0.0
