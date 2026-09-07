"""5th-gen Haldex electrohydraulic AWD clutch — spec constants (ASSUMPTION: no public Gen5-specific torque-split numbers; behavior modeled on known Haldex characteristics)."""

# Researched (forums, 2026-08-18): a 2005 Volvo PR release (quoted verbatim in
# a SwedeSpeed thread, archived text, not paraphrased) is a genuine primary
# source stating "in normal driving, with the AWD system inactive, 95 per
# cent of power is delivered to the front wheels... the system can transfer
# up to 95 per cent of the power to the rear." That's real Volvo language,
# but it describes the Gen2/3/4 coupling in P2-platform cars (S40/V50/S60/
# S80/V70/XC70/first-gen XC90) circa 2005 -- not confirmed to carry over
# unchanged to the Gen5 coupling in this car's SPA-platform (2015+) XC90.
# Note: "BorgWarner" and "Haldex" are NOT competing suppliers here -- BorgWarner
# acquired Haldex Traction Systems in 2013, so "BorgWarner-supplied AWD
# coupling" (industry press) and "Haldex Gen5" (enthusiast/parts-catalog
# naming, e.g. IPD's "AOC Haldex 5" kits for S60/S80/XC60/XC70/XC90) refer to
# the same hardware lineage, not a naming error in this codebase.
# Other forum claims found (100/0 until slip; 70/30 stock split; 50/50 when
# fully clamped) came only as AI-generated search-result summaries of
# SwedeSpeed threads, mutually contradictory, and not traceable to primary
# source text (the threads themselves are paywalled/bot-blocked) -- treated
# as unreliable and NOT used. Net effect: this 0.90 stays an ASSUMPTION, but
# it's now corroborated in shape (strongly front-biased baseline, same order
# of magnitude as the verified 0.95 for the predecessor hardware) rather than
# a bare guess.
BASE_FRONT_BIAS = 0.90  # nominal FWD-biased split under no slip
MIN_FRONT_BIAS = 0.50   # max rear engagement under high slip
SLIP_FOR_MIN_BIAS_RAD_S = 3.0  # front/rear axle slip (rad/s, wheel-equiv) at which bias bottoms out

# Haldex Gen 3+ (this car's Gen 5 included) is documented as PROACTIVE — it
# pre-tensions the clutch and engages the rear axle based on anticipated
# demand (throttle position, at low speed where wheelspin risk is highest),
# not only reactively after slip is already detected. Researched, not
# assumed: a purely reactive model (the only path before this) let a launch
# spin up before AWD engagement caught up, especially after correcting the
# front/rear weight split to the real, more rear-biased 52/48 figure.
# ASSUMPTION values for the anticipatory response shape (no public data).
PROACTIVE_SPEED_THRESHOLD_MPS = 15.0  # anticipatory engagement fades out above this speed

