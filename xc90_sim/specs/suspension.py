"""
2016 XC90 (SPA platform) suspension — spec constants.

Layout is documented by Volvo: double-wishbone front, "Integral Axle"
multi-link rear. CORRECTED 2026-08-19: the non-Four-C rear is NOT a steel
coil spring -- Volvo's own press material (media.volvocars.com model
overview) and corroborating trade coverage (Green Car Congress, PlasticsToday,
on the Henkel-resin composite) confirm the standard rear suspension uses a
transverse fiber-reinforced composite leaf spring (saves ~4.5kg vs. a coil
design); only the front is a MacPherson-strut coil spring. This sim still
represents both ends as a single linear spring rate -- physically reasonable
for a heave/roll model (a leaf spring's vertical rate is well-approximated as
linear near ride height, same as a coil), so no equation changes were needed,
just this corrected description. Spring rates, damper rates, unsprung mass,
and roll stiffness aren't published — they're derived below from plausible
ride-frequency/damping-ratio targets for a comfort-tuned crossover, flagged
ASSUMPTION. This module also owns static weight distribution and CG height,
since both are inputs to the suspension's load-transfer model, not body/aero
properties.
"""

from . import chassis as _chassis

FRONT_WEIGHT_FRACTION = 0.52  # published: 52/48 front/rear (The Truth About Cars technical
# review, comparing it directly to the Mercedes GL/GLE's known split) — replaces an earlier
# 0.55 ASSUMPTION guess.
CG_HEIGHT_M = 0.62  # ASSUMPTION: center-of-gravity height (not published for this car;
# researched — no magazine or Volvo source publishes this for the XC90).
# Re-checked 2026-08-19: NHTSA's SafetyRatings API (VehicleId 10908, "2016
# Volvo XC90 T6 SUV AWD") gives a real rollover-probability figure (17.9%,
# 4-star rollover rating) which is DERIVED from the Static Stability Factor
# this constant could be back-calculated from (SSF = track / (2*CG_height))
# — but NHTSA's raw SSF filings (docket NHTSA-2001-9663) 403'd on every
# fetch attempt this session. Worth one more try from an unblocked network;
# not backed into from the rollover% alone since that requires the exact
# logistic-regression coefficients, which weren't reliably confirmed either.

FRONT_TRACK_M = 1.663  # published spec, approx
REAR_TRACK_M = 1.663   # published spec, approx

# Distances from CG to each axle, from the wheelbase + static weight split
# (heavier end sits closer to the CG, by the lever/moment-balance relation).
DIST_CG_TO_FRONT_M = _chassis.WHEELBASE_M * (1.0 - FRONT_WEIGHT_FRACTION)
DIST_CG_TO_REAR_M = _chassis.WHEELBASE_M * FRONT_WEIGHT_FRACTION

# ASSUMPTION: pitch/roll moments of inertia aren't published; these are
# plausible ballpark figures for a ~2100 kg crossover of this footprint.
PITCH_INERTIA_KGM2 = 3600.0
ROLL_INERTIA_KGM2 = 750.0

UNSPRUNG_MASS_PER_CORNER_KG = 45.0  # ASSUMPTION: wheel+tire+hub+brake+control-arm share.
# Checked 2026-08-19: no teardown, vendor spec, or forum corner-weighing for
# the XC90 (any trim/year) publishes this. SwedeSpeed threads give OEM wheel
# weight alone (19" ~28 lb, 18" ~22-25 lb) but not a full corner breakdown.
# Still an unverified guess.

# ASSUMPTION: comfort-biased ride frequencies (Hz) and damping ratio, typical
# for this class of crossover SUV; spring/damper rates are derived from them.
FRONT_RIDE_FREQUENCY_HZ = 1.3
REAR_RIDE_FREQUENCY_HZ = 1.4
DAMPING_RATIO = 0.3

_TOTAL_MASS_KG = _chassis.CURB_MASS_KG
_FRONT_AXLE_MASS_KG = _TOTAL_MASS_KG * FRONT_WEIGHT_FRACTION
_REAR_AXLE_MASS_KG = _TOTAL_MASS_KG * (1.0 - FRONT_WEIGHT_FRACTION)
FRONT_SPRUNG_MASS_PER_CORNER_KG = _FRONT_AXLE_MASS_KG / 2.0 - UNSPRUNG_MASS_PER_CORNER_KG
REAR_SPRUNG_MASS_PER_CORNER_KG = _REAR_AXLE_MASS_KG / 2.0 - UNSPRUNG_MASS_PER_CORNER_KG

FRONT_SPRING_RATE_N_PER_M = (2 * 3.14159265 * FRONT_RIDE_FREQUENCY_HZ) ** 2 * FRONT_SPRUNG_MASS_PER_CORNER_KG
REAR_SPRING_RATE_N_PER_M = (2 * 3.14159265 * REAR_RIDE_FREQUENCY_HZ) ** 2 * REAR_SPRUNG_MASS_PER_CORNER_KG

FRONT_DAMPER_C_NS_PER_M = 2 * DAMPING_RATIO * (FRONT_SPRING_RATE_N_PER_M * FRONT_SPRUNG_MASS_PER_CORNER_KG) ** 0.5
REAR_DAMPER_C_NS_PER_M = 2 * DAMPING_RATIO * (REAR_SPRING_RATE_N_PER_M * REAR_SPRUNG_MASS_PER_CORNER_KG) ** 0.5

BUMP_TRAVEL_M = 0.09    # ASSUMPTION: jounce travel to bump stop
DROOP_TRAVEL_M = 0.08   # ASSUMPTION: rebound travel to droop stop
BUMP_STOP_STIFFNESS_MULTIPLIER = 12.0  # ASSUMPTION: sharp progressive rate increase at the stop

# Anti-roll bar roll stiffness, front-biased (pushes the balance toward
# understeer, Volvo's default handling philosophy). ASSUMPTION — no public data
# converts cleanly to these units. Checked 2026-08-19: IPD's own spec table
# for its 25mm P5-XC90 rear bar (ipdusa.com part 142483) states OEM rear =
# 22mm diameter / 95 lbf-in stiffness (their 25mm bar = 206 lbf-in, +116%,
# which checks out arithmetically) — a real, XC90-specific rear stock spec.
# Not converted into REAR_ARB_ROLL_STIFFNESS_NM_PER_RAD directly: IPD's test
# rig geometry (lever arm / mounting method behind "lbf-in") isn't published,
# and torsional bar-rate vs. at-wheel roll-stiffness rate aren't the same
# quantity without knowing that geometry — so this is corroborating evidence
# a real 22mm rear bar exists, not a sourced replacement number. No front bar
# diameter was found from any vendor (only marketing copy for upgrade kits,
# no stock baseline stated).
FRONT_ARB_ROLL_STIFFNESS_NM_PER_RAD = 15000.0
REAR_ARB_ROLL_STIFFNESS_NM_PER_RAD = 8000.0

# Toe change vs. corner compression (relative to static ride height),
# positive = bump/compression. Camber is derived from actual linkage
# hardpoints instead (see specs/linkage.py, suspension/linkage_geometry.py);
# toe uses a flat linear gain since a dedicated toe-control link isn't
# captured by that same swing-arm model. ASSUMPTION — no public XC90 data —
# but representative of each suspension type's real character: Volvo's
# multi-link rear ("Integral Axle") is specifically designed for passive
# toe-in under cornering/braking load, hence the larger rear gain.
FRONT_TOE_GAIN_DEG_PER_M = 2.0   # toe-in under bump
REAR_TOE_GAIN_DEG_PER_M = 4.0    # toe-in under bump, stronger (by design)
