"""
Fuel tank: level in liters, drawn down by REAL fuel mass burned (from the
cylinder-level combustion model's per-cycle fuel injection — see
Engine.total_fuel_burned_kg), not an estimated MPG figure. Simulation
converts the engine's cumulative fuel-burned mass to a volume via gasoline
density and deducts it each tick — this is genuine fuel consumption
falling out of real combustion physics, not a separately-modeled MPG
assumption layered on top.

Also tracks real fuel chemistry/aging — ethanol content, octane rating,
and time since fill — and derives the actual combustion-relevant
properties (effective LHV, effective stoichiometric AFR, an octane
shortfall relative to what this engine wants, and a staleness derate)
from them. These feed back into Engine's combustion model (see
Simulation.step()), so putting cheap low-octane gas in the tank, or
letting it sit for months, has a real, connected effect on how the engine
actually runs — not just a cosmetic "fuel type" label.
"""

from ..specs import fuel as specs
from ..specs import cylinder as cyl_specs


class FuelTank:
    def __init__(self, level_l=None, ethanol_fraction=None, octane_aki=None):
        self.level_l = specs.TANK_CAPACITY_L if level_l is None else level_l
        self.ethanol_fraction = specs.DEFAULT_ETHANOL_FRACTION if ethanol_fraction is None else ethanol_fraction
        self.octane_aki = specs.DEFAULT_OCTANE_AKI if octane_aki is None else octane_aki
        self.days_since_fill = 0.0

    def consume_kg(self, fuel_mass_kg):
        self.level_l = max(0.0, self.level_l - fuel_mass_kg / specs.GASOLINE_DENSITY_KG_PER_L)

    def add_fuel_l(self, liters, ethanol_fraction=None, octane_aki=None):
        """Refueling. Optionally specify the new fuel's ethanol_fraction/
        octane_aki (defaults to whatever's already in the tank, i.e.
        topping off with "the same stuff") — always resets the age clock,
        since topping off is treated as diluting old fuel back to fresh
        enough rather than tracking a true weighted-average blend age."""
        self.level_l = min(specs.TANK_CAPACITY_L, self.level_l + max(0.0, liters))
        if ethanol_fraction is not None:
            self.ethanol_fraction = ethanol_fraction
        if octane_aki is not None:
            self.octane_aki = octane_aki
        self.days_since_fill = 0.0

    def step(self, dt):
        self.days_since_fill += dt / 86400.0

    def low_fuel_warning(self):
        return self.level_l <= specs.LOW_FUEL_WARNING_L

    def level_fraction(self):
        return self.level_l / specs.TANK_CAPACITY_L

    def effective_lhv_j_per_kg(self):
        """Blended lower heating value — ethanol carries meaningfully less
        energy per unit mass than gasoline."""
        return (
            (1.0 - self.ethanol_fraction) * cyl_specs.FUEL_LHV_J_PER_KG
            + self.ethanol_fraction * specs.ETHANOL_LHV_J_PER_KG
        )

    def effective_stoich_afr(self):
        """Blended stoichiometric air-fuel ratio — ethanol needs much less
        air per unit fuel mass than gasoline."""
        return (
            (1.0 - self.ethanol_fraction) * cyl_specs.STOICHIOMETRIC_AFR
            + self.ethanol_fraction * specs.ETHANOL_STOICH_AFR
        )

    def effective_octane_aki(self):
        return self.octane_aki + self.ethanol_fraction * specs.ETHANOL_OCTANE_AKI_BOOST_PER_FRAC

    def octane_boost_derate_frac(self):
        """Real knock-protection response: how much the ECU has to cut
        boost when the actual fuel falls short of what this engine wants.
        0 for anything at or above the required octane."""
        shortfall = max(0.0, specs.OCTANE_REQUIRED_AKI - self.effective_octane_aki())
        return min(specs.MAX_LOW_OCTANE_BOOST_DERATE_FRAC, shortfall * specs.OCTANE_DERATE_PER_AKI_POINT_SHORT)

    def staleness_combustion_derate_frac(self):
        """Real effect of fuel sitting too long: light volatile fractions
        evaporate and oxidation begins, hurting combustion efficiency —
        the practical "won't run right after sitting all winter" symptom."""
        if self.days_since_fill <= specs.GASOLINE_STALE_ONSET_DAYS:
            return 0.0
        if self.days_since_fill >= specs.GASOLINE_STALE_FULL_DEGRADED_DAYS:
            return specs.MAX_STALE_COMBUSTION_DERATE_FRAC
        span = specs.GASOLINE_STALE_FULL_DEGRADED_DAYS - specs.GASOLINE_STALE_ONSET_DAYS
        frac_through = (self.days_since_fill - specs.GASOLINE_STALE_ONSET_DAYS) / span
        return frac_through * specs.MAX_STALE_COMBUSTION_DERATE_FRAC
