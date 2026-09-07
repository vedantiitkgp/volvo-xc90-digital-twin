"""Body control module — spec constants (doors, hood, power tailgate, central locking)."""

DOORS = ("fl", "fr", "rl", "rr")

# T6 Momentum comes standard with a hands-free power tailgate (kick-sensor
# activated liftgate). ASSUMPTION: actuation time isn't published by Volvo;
# a plausible full open/close cycle time for this class of power liftgate.
TAILGATE_ACTUATION_TIME_S = 6.0

# Speed-based auto door lock ("Auto door lock," a real, owner's-manual-
# documented Volvo feature, enabled by default): all doors lock once the
# car is moving above a threshold speed, provided every door is shut.
# ASSUMPTION: the exact threshold isn't published; a commonly-cited value
# for this class of feature across manufacturers.
AUTO_LOCK_SPEED_MPS = 4.5  # ~10 mph

# ASSUMPTION: real window motor speed isn't published; a plausible full
# up/down time (~4s) for this class of power window.
WINDOW_MOVE_RATE_PCT_PER_S = 25.0

# Real turn signals flash at a regulated rate, typically 60-120 flashes/min;
# 1.5 Hz (90/min) is a common real-world figure for this class of vehicle.
INDICATOR_BLINK_HZ = 1.5

# --- Wipers (front + rear) ---
# ASSUMPTION: none of these cycle times are published; plausible values for
# this class of wiper motor. Front has 3 active speeds; rear (tailgate
# glass) is simpler, same as most real cars.
FRONT_WIPER_CYCLE_S = {"intermittent": 4.0, "low": 1.3, "high": 0.65}
REAR_WIPER_CYCLE_S = {"intermittent": 5.0, "on": 1.3}
WIPER_SWEEP_DURATION_S = 0.4  # ASSUMPTION: how long one physical sweep takes, vs. the rest/pause

# --- Windshield washer fluid ---
# ASSUMPTION: neither is published; plausible for this class of vehicle.
WASHER_FLUID_CAPACITY_L = 3.5
WASHER_FLUID_SPRAY_VOLUME_L = 0.015  # per spray/wipe-with-fluid event
WASHER_FLUID_LOW_WARNING_L = 0.3

# --- Panoramic sunroof: glass panel + independent electric sunshade/cover ---
# ASSUMPTION: neither actuation time is published; plausible values for
# this class of power sunroof/shade.
SUNROOF_GLASS_ACTUATION_TIME_S = 15.0
SUNROOF_SHADE_ACTUATION_TIME_S = 8.0
