"""
DSTC (Volvo's name for its bundled traction/stability control system) —
spec constants. No public calibration data exists for this; thresholds are
plausible values that engage before the tire's peak-grip slip point
(~0.15-0.2, see specs.tire), leaving margin, same as a real system tuned to
intervene before the driver reaches the limit rather than exactly at it.
"""

# Traction control (engine torque cut on driven-wheel slip during acceleration).
# Threshold set at this tire model's own measured peak-grip slip ratio
# (~0.18, confirmed by directly sampling TireModel.forces() — see STATUS.md)
# rather than cutting in early: a real TCS lets slip build TO the tire's
# maximum before intervening, since some slip is required for peak traction
# at all. The floor was raised from an earlier, more severe 0.15 — real
# production TCS calibration prioritizes forward progress over eliminating
# slip entirely, using ignition retard/per-cylinder cuts more than a blunt
# power cut.
TCS_SLIP_THRESHOLD = 0.18
TCS_TORQUE_CUT_GAIN = 3.0          # proportional cut beyond threshold
TCS_MIN_TORQUE_FRACTION = 0.35     # never cuts torque all the way to zero
# Slip = (wheel - ref)/ref blows up at low ref speed even for a small absolute
# difference (sensor quantization noise included) — floor the denominator at
# a speed high enough that this doesn't cause spurious triggers, but TCS must
# still work right from a standing start, so this can't just disable outright.
TCS_MIN_REFERENCE_KPH = 8.0

# ABS (per-wheel brake release/reapply on lockup during braking).
ABS_LOCKUP_SLIP_THRESHOLD = -0.25  # engage release below this (more negative = more locked)
ABS_REAPPLY_SLIP_THRESHOLD = -0.10  # fully reapply once slip recovers above this
ABS_RELEASE_FRACTION = 0.15        # residual brake torque fraction during a release pulse
# Below this, wheel-speed sensing is unreliable (quantization noise dominates
# a near-zero true speed) and there's no real stopping-distance benefit to
# ABS modulation anyway — real ABS disables itself in this same regime.
ABS_MIN_SPEED_KPH = 5.0

# ESC (single-wheel corrective braking on yaw-rate error vs. a kinematic reference).
ESC_MIN_SPEED_MPS = 3.0             # below this, the kinematic reference is unreliable
ESC_YAW_RATE_DEADBAND_RAD_S = 0.05  # ~2.9 deg/s tolerance before intervening
ESC_BRAKE_GAIN_NM_PER_RAD_S = 800.0
ESC_MAX_BRAKE_TORQUE_NM = 600.0
