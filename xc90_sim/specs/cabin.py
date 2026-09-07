"""Cabin/interior — spec constants (HVAC, parking sensors, seats, storage, pedals, infotainment)."""

from . import chassis as _chassis

# --- HVAC (climate control) ---
# ASSUMPTION: no published thermal model for this cabin exists; plausible
# lumped-parameter figures for a 3-row SUV cabin of this size (first-order
# thermal system: one effective thermal mass, one effective heat-loss
# coefficient to ambient — a real cabin has many surfaces/zones, this
# collapses them to the two numbers that matter for a heave/pitch-style
# lumped model, same simplification philosophy as elsewhere in this project).
# Tuned so a full-fan HVAC noticeably changes cabin temp within a few
# minutes (real-car-like responsiveness), not tens of minutes — 50 kJ/K
# is well above pure cabin air's thermal mass (~4 kJ/K) to account for trim/
# seat material the air exchanges heat with, but far below the vehicle's
# structural mass, which the HVAC doesn't meaningfully heat/cool in a drive.
CABIN_THERMAL_MASS_KJ_PER_K = 50.0
CABIN_AMBIENT_UA_W_PER_K = 45.0
HVAC_MAX_HEATING_W = 5000.0
HVAC_MAX_COOLING_W = 4000.0
MAX_FAN_SPEED = 7  # matches Volvo's typical 1-7 manual fan speed display
MIN_TARGET_TEMP_C = 16.0
MAX_TARGET_TEMP_C = 28.0

# --- Parking sensors (front/rear ultrasonic "Park Assist") ---
# ASSUMPTION: exact detection ranges aren't published; typical figures for
# ultrasonic park-assist systems of this era/class.
PARK_SENSOR_MAX_RANGE_M = 1.5
PARK_SENSOR_NEAR_M = 0.6
PARK_SENSOR_CRITICAL_M = 0.3

# Low-speed collision mitigation: connects the parking sensors to the
# engine/brakes, not just a dashboard warning — a real, if simplified,
# version of the low-speed automatic braking Volvo's City Safety provides.
# ASSUMPTION: not published; a moderate (not full-panic) automatic brake
# application, since this is meant to prevent a slow parking-speed bump,
# not perform an emergency stop.
PARK_ASSIST_AUTO_BRAKE_FRAC = 0.4

# --- Park Assist Pilot (semi-autonomous parallel parking) ---
# Real Volvo Park Assist Pilot's actual path-planning is proprietary and
# unpublished. What's modeled here is a real, simplified two-phase
# geometric parallel-park technique -- turn to full lock, reverse until the
# car reaches roughly a 30-40 degree angle to the curb, then countersteer
# to full lock the other way and reverse until parallel again -- which is
# the same technique driving instruction describes for a HUMAN doing this
# maneuver by hand, not a fabricated algorithm, but also not a match for
# Volvo's real (likely continuously-optimized, not fixed-angle) path.
# ASSUMPTION: none of these specific numbers are published.
PARK_PILOT_SCAN_RANGE_M = 3.0  # side sensor range while scanning for a gap
PARK_PILOT_MIN_SPOT_LENGTH_M = _chassis.WHEELBASE_M + 1.2
PARK_PILOT_PHASE1_HEADING_DEG = 35.0
PARK_PILOT_COMPLETE_HEADING_TOLERANCE_DEG = 3.0
PARK_PILOT_CREEP_SPEED_MPS = 1.0  # ~3.6 kph -- real Park Assist Pilot creeps slowly

# --- Oil life monitor ---
# A real oil life monitor counts down miles since the last reset (a
# service-menu action after an actual oil change) -- it is NOT a literal
# continuous oil-quality sensor most cars don't have. ASSUMPTION: neither
# figure is published for this specific engine/oil combination; commonly
# cited interval/warning-threshold figures for this class of feature.
OIL_LIFE_INTERVAL_MILES = 10000.0
OIL_LIFE_WARNING_PCT = 15.0

# --- Blind Spot Information System (BLIS) ---
# ASSUMPTION: exact activation speed isn't published; real BLIS-type systems
# commonly disable below ~10 kph to avoid parking-lot false positives.
BLIS_MIN_SPEED_MPS = 2.8  # ~10 kph

# --- Seats (2-3-2, 7 seats total) ---
SEAT_POSITIONS = ("driver", "front_passenger", "row2_left", "row2_right", "row3_left", "row3_right")
# T6 Momentum standard equipment includes heated front seats; heated 2nd-row
# seats are an option on higher trims (Inscription) — ASSUMPTION for this
# specific VIN (not confirmed via the CARFAX/build sheet) that rear heating
# isn't fitted. Update this if the owner confirms otherwise.
FRONT_SEATS_HEATED = True
REAR_SEATS_HEATED = False
SEAT_HEAT_LEVELS = 3  # off + 3 levels, matches Volvo's typical 3-bar seat-heat display

# --- Cargo / storage ---
CARGO_VOLUME_BEHIND_ROW3_L = 314.0  # published spec
CARGO_VOLUME_MAX_L = 1858.0  # published spec, 2nd/3rd rows folded flat
GLOVE_BOX_VOLUME_L = 5.0  # ASSUMPTION: not published, plausible for this class

# --- Pedals ---
# ASSUMPTION: pedal travel distance isn't published; plausible values for
# this class of car, used only to derive a physical mm reading from the 0-100%
# command already driving the engine/brake models — doesn't change any physics.
ACCELERATOR_MAX_TRAVEL_MM = 90.0
BRAKE_MAX_TRAVEL_MM = 100.0
