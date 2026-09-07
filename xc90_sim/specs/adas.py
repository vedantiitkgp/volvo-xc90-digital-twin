"""
Radar/camera-based ADAS — spec constants for Adaptive Cruise Control (ACC)
and lane-keeping assist (Pilot-Assist-style steering nudge).

ASSUMPTION throughout: exact factory tuning (radar range, time-gap steps,
steering-assist gain/limit) isn't published for this car; these are
plausible values for this class of system.
"""

# Forward radar
RADAR_MAX_RANGE_M = 150.0

# Real Pilot Assist / ACC offers a few selectable follow-distance settings
# (time gap, not a fixed meters figure, since the safe gap scales with
# speed) -- named steps rather than a single number.
FOLLOW_TIME_GAP_S = {"close": 1.0, "medium": 1.5, "far": 2.0}
ACC_MIN_FOLLOW_DISTANCE_M = 3.0  # standoff even at a dead stop / very low speed
ACC_GAP_ERROR_GAIN = 0.15  # (m/s target-speed correction) per meter of gap error

# Lane-keeping assist (steering nudge, not a robot driver): real Pilot
# Assist applies light, bounded corrective steering torque and backs off
# for any real driver steering input -- it's an assist, not an autopilot.
LKA_LATERAL_GAIN_DEG_PER_M = 8.0
LKA_HEADING_GAIN_DEG_PER_RAD = 25.0
LKA_MAX_CORRECTIVE_DEG = 12.0
# A driver input beyond this is treated as a deliberate override (turning,
# an intentional lane change) -- LKA backs off entirely rather than fighting it.
LKA_DRIVER_OVERRIDE_DEG = 45.0
