"""
Tire force model (simplified "Magic Formula" / Pacejka-style) — spec constants.

No manufacturer data is published for the OEM 235/55R19 touring tire, so
these shape factors (B = stiffness, C = shape, E = curvature) use the
illustrative generic-passenger-tire values commonly quoted from Pacejka's own
textbook examples, not measurements of this specific tire. Peak force is
D = mu * Fz, using xc90_sim.specs.chassis.TIRE_FRICTION_COEFFICIENT.
"""

LONG_B = 10.0   # ASSUMPTION: longitudinal stiffness factor
LONG_C = 1.9    # ASSUMPTION: longitudinal shape factor
LONG_E = 0.97   # ASSUMPTION: longitudinal curvature factor

LAT_B = 8.0     # ASSUMPTION: lateral stiffness factor
LAT_C = 1.3     # ASSUMPTION: lateral shape factor
LAT_E = -1.6    # ASSUMPTION: lateral curvature factor

# Regularizes slip-ratio/slip-angle calculations at near-zero speed, where
# v-in-the-denominator formulas are singular.
SLIP_SPEED_EPSILON_MPS = 1.0

# Real tires don't reach their kinematically-implied slip instantly — the
# contact patch has to deform first, which takes a few tenths of a meter of
# rolling distance ("relaxation length"). Modeling that lag isn't just more
# realistic: with this tire curve's peak-then-falloff shape, computing slip
# instantaneously each tick creates a tight, stiff feedback loop that
# explicit-Euler integration cannot handle stably at any reasonable
# timestep. ASSUMPTION values, typical for a passenger tire.
LONGITUDINAL_RELAXATION_LENGTH_M = 0.4
LATERAL_RELAXATION_LENGTH_M = 0.5

# Camber thrust: a cambered tire generates lateral force even at zero slip
# angle. Real camber stiffness is typically ~1/10-1/5 of cornering
# stiffness per radian — this coefficient scales normal load directly
# (Fy_camber = COEFFICIENT * camber_rad * Fz), matching that ratio.
# ASSUMPTION — no published data for this tire.
CAMBER_THRUST_COEFFICIENT = 0.06

# --- TPMS (Tire Pressure Monitoring System) ---
# ASSUMPTION: this specific VIN's door-placard cold-tire-pressure spec isn't
# available; 36 psi is a commonly cited figure for this class/tire size, not
# independently verified for this exact trim/wheel combination.
RECOMMENDED_COLD_PRESSURE_PSI = 36.0
# FMVSS 138 (US federal standard): TPMS must warn when any tire is 25% or
# more below the vehicle's recommended cold pressure — this threshold is
# real regulation, not a guess.
TPMS_WARNING_THRESHOLD_FRAC = 0.75

