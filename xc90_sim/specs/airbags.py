"""
Airbags/SRS (Supplemental Restraint System) — spec constants.

ASSUMPTION throughout: real deployment logic is a proprietary algorithm
integrating the shape of the crash pulse over tens of milliseconds against
a "safing sensor," not a single instantaneous g threshold. This sim has no
collision/contact physics (no obstacles to actually crash into), so a
simple instantaneous-g threshold against the real body-frame accelerometer
data (VehicleBody.ax_mps2/ay_mps2) is what's available and is honestly a
coarse approximation, not a real crash-pulse discriminating algorithm.
"""

GRAVITY_MS2 = 9.80665

# Real published deployment thresholds are not available for this specific
# car (they're proprietary). These are plausible single-instant g levels,
# well above anything seen in normal driving or hard braking (this project's
# own regression trip peaks around 0.6g longitudinal, 0.3g lateral).
FRONTAL_DEPLOY_THRESHOLD_G = 8.0
SIDE_DEPLOY_THRESHOLD_G = 5.0

# ASSUMPTION: typical dash-light bulb-check duration at power-on.
SRS_BULB_CHECK_DURATION_S = 3.0
