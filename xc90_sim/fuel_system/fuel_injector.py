"""
Fuel injector (direct injection — this is a real GDI engine): converts a
commanded fuel mass into an actual pulse width in milliseconds via the
injector's rated flow rate, the real quantity an ECU computes and commands
— not just a fuel mass appearing from nowhere. Low fuel-rail pressure
derates achievable flow, the same real coupling a GDI system has.
"""

from ..specs import cylinder as specs


class FuelInjector:
    def __init__(self):
        self.last_pulse_width_ms = 0.0
        self.last_delivered_fuel_kg = 0.0

    def inject(self, commanded_fuel_kg, fuel_pressure_frac=1.0):
        """fuel_pressure_frac (0..1): actual/target fuel rail pressure. Returns
        the actually-delivered fuel mass (kg), which can fall short of what
        was commanded if the pulse width hits its physical ceiling."""
        effective_flow_kg_per_s = specs.INJECTOR_FLOW_RATE_KG_PER_S * max(0.1, fuel_pressure_frac)
        pulse_width_ms = (commanded_fuel_kg / effective_flow_kg_per_s) * 1000.0
        self.last_pulse_width_ms = min(specs.INJECTOR_MAX_PULSE_WIDTH_MS, pulse_width_ms)
        self.last_delivered_fuel_kg = effective_flow_kg_per_s * (self.last_pulse_width_ms / 1000.0)
        return self.last_delivered_fuel_kg
