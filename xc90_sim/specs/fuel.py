"""Fuel system — spec constants."""

TANK_CAPACITY_L = 71.0  # published (volvocars.com support), 18.8 US gal
GASOLINE_DENSITY_KG_PER_L = 0.745  # real, typical for US-spec gasoline (varies slightly by blend/season)

# ASSUMPTION: not published; typical for this class of fuel gauge (most
# don't read perfectly linearly against volume due to tank shape, but a
# flat/linear reading is a standard, reasonable simplification here).
LOW_FUEL_WARNING_L = 8.0

# --- Fuel chemistry/aging ---
# Real published constants (ethanol energy content/AFR are standard,
# well-documented chemistry, not specific to this car).
ETHANOL_LHV_J_PER_KG = 26.8e6   # ethanol's lower heating value -- real, ~61% of gasoline's per unit mass
ETHANOL_STOICH_AFR = 9.0        # real stoichiometric air-fuel ratio for pure ethanol
# ASSUMPTION: US pump gasoline is commonly E10 (10% ethanol) by regulation
# in most states; this car isn't flex-fuel, so E10 is the realistic default
# rather than pure E0.
DEFAULT_ETHANOL_FRACTION = 0.10
# ASSUMPTION: Volvo's Drive-E T6 (turbo+supercharger) is commonly cited as
# requiring/recommending premium (91 AKI/95 RON) fuel for this class of
# high-compression, boosted engine -- not independently verified against a
# primary Volvo source for this exact car, flagged ASSUMPTION rather than
# treated as confirmed.
OCTANE_REQUIRED_AKI = 91.0
DEFAULT_OCTANE_AKI = 91.0  # assumes the driver actually buys the recommended premium grade
# ASSUMPTION: ethanol has a real, higher octane rating than gasoline (RON
# ~109) -- blending some in measurably raises a blend's effective octane.
# Value here is a plausible per-unit-ethanol-fraction boost, not derived
# from a specific fuel's published blend curve.
ETHANOL_OCTANE_AKI_BOOST_PER_FRAC = 25.0  # e.g. +2.5 AKI points at E10 (0.10 fraction)
# ASSUMPTION: real ECU knock protection retards timing/cuts boost when
# actual octane (after any ethanol boost) falls short of what the engine
# wants -- a genuine, connected effect, not a flat power number regardless
# of fuel used. Values are plausible for this class of knock-protected
# boosted engine, not measured.
MAX_LOW_OCTANE_BOOST_DERATE_FRAC = 0.20  # ceiling: worst-case knock-protection boost cut
OCTANE_DERATE_PER_AKI_POINT_SHORT = 0.04  # fractional boost cut per AKI point below required
# ASSUMPTION: gasoline degrades in storage (light volatile fractions
# evaporate, oxidation begins) -- real practical guidance is measurable
# problems starting within a few months, worse for ethanol-blended fuel
# (hygroscopic). Reset to "fresh" (0 days) on every add_fuel_l() call --
# topping off is treated as diluting old fuel back to fresh enough, a
# reasonable simplification rather than tracking a true weighted-average
# blend age.
GASOLINE_STALE_ONSET_DAYS = 90.0
GASOLINE_STALE_FULL_DEGRADED_DAYS = 365.0
MAX_STALE_COMBUSTION_DERATE_FRAC = 0.15  # ceiling: how much very stale fuel can derate combustion efficiency
