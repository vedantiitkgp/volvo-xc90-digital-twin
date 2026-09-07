"""
Belt-driven accessories, electrical charging, and fuel delivery hardware —
spec constants. Real, verified facts noted individually; everything else
is an ASSUMPTION (proprietary/unpublished for this exact car).

Note: this car has ELECTRIC power-assisted steering (see specs/steering.py)
-- there is no belt-driven hydraulic power-steering pump, unlike older
Volvos. The serpentine belt here drives the alternator and AC compressor
only, not a steering pump.
"""

# --- Timing belt ---
# The 2:1 camshaft:crankshaft ratio is an exact mechanical fact for any
# 4-stroke engine (one full 4-stroke cycle = 2 crank revolutions = 1
# camshaft revolution), not an assumption. The specific sprocket TOOTH
# COUNTS below are ASSUMPTION (plausible real-looking numbers preserving
# the exact 2:1 ratio; this project's own real teardown data isn't
# available) -- see wear/wear_model.py's "timing_belt" entry for the real,
# verified 150,000mi/12yr replacement interval.
CRANK_SPROCKET_TEETH = 36
CAM_SPROCKET_TEETH = 72  # exactly 2x -- the real, non-negotiable ratio

# --- Accessory (serpentine) belt ---
# ASSUMPTION: this specific car's interval isn't documented in
# service_history.py; a commonly-cited interval for this class of belt —
# see wear/wear_model.py's "accessory_belt" entry.

# --- Alternator ---
# ASSUMPTION: none of these are published for this car; plausible values
# for this class of vehicle's charging system.
ALTERNATOR_EFFICIENCY = 0.55  # real automotive alternators are commonly cited around 50-60%
ALTERNATOR_BASELINE_LOAD_W = 80.0  # engine management / sensors / always-on electronics

# AC compressor: mechanical (belt-driven refrigerant compressor), not
# electrical -- a separate real load from everything the alternator
# supplies. ASSUMPTION: typical for this class of compressor when its
# clutch is actively engaged (HVAC calling for active cooling).
AC_COMPRESSOR_LOAD_NM_AT_1000_RPM = 8.0

# Real, approximate wattages for this car's actual electrical consumers —
# ASSUMPTION per item (not measured for this VIN), but the *list* itself
# (which consumers exist, LED-era headlight wattages being much lower than
# older halogen figures) reflects this being a 2016 car with LED lighting,
# not a generic guess.
HEADLIGHT_LOW_BEAM_W = 60.0
HEADLIGHT_HIGH_BEAM_W = 40.0  # additional, on top of low beam
DRL_W = 20.0
PARKING_LIGHT_W = 10.0
HVAC_BLOWER_MAX_W = 250.0  # at max fan speed; scales with fan_speed/MAX_FAN_SPEED
SEAT_HEATER_MAX_W = 80.0  # per seat, at max heating level
INFOTAINMENT_W = 30.0
WIPER_MOTOR_W = 40.0
HORN_W = 60.0
FOG_LIGHT_W = 30.0
DOME_LIGHT_W = 5.0
FUEL_PUMP_ELECTRICAL_W = 65.0  # the lift pump below is itself an electrical load
# ASSUMPTION: typical electric radiator cooling fan draw for this class of
# car — was never actually connected to the electrical system before (the
# fan's real current draw is meaningful, ~15-20A, and belongs in the same
# demand accounting as every other consumer above).
COOLING_FAN_ELECTRICAL_W = 200.0
# ASSUMPTION: typical small electric brake-booster vacuum pump draw — see
# specs/chassis.py's vacuum-system constants for why this car has one.
VACUUM_PUMP_ELECTRICAL_W = 40.0

# --- 12V battery ---
# ASSUMPTION: not published for this VIN. AGM (not flooded lead-acid) is a
# real, well-known requirement for cars with genuine Auto Start/Stop (see
# xc90_sim.electrical.AutoStopStart) -- AGM tolerates the frequent engine-
# off/restart cycling that would prematurely wear a flooded battery. Sized
# plausibly for this class of vehicle, not measured.
BATTERY_CAPACITY_AH = 70.0
BATTERY_NOMINAL_VOLTAGE = 12.6
BATTERY_LOW_CHARGE_WARNING_FRAC = 0.3
BATTERY_MAINTENANCE_CHARGE_W = 150.0  # extra alternator output beyond immediate demand, to charge the battery
CRANKING_DISCHARGE_W = 1000.0  # real: starter motor draws a lot of current
MIN_CHARGE_FRAC_TO_START = 0.15  # a real, connected failure mode: too weak to crank

# --- Support (auxiliary) battery ---
# Real, confirmed feature (checked 2026-08-24 via SwedeSpeed/owner-forum
# reports of replacing this exact car's "auxiliary battery to fix start/
# stop"): this car carries a SECOND, smaller battery specifically to buffer
# the electronics bus (infotainment, instrument cluster) through every
# engine restart. Without it, the starter's big current draw off the main
# battery would sag system voltage enough to reset sensitive electronics —
# a real, documented failure mode when this battery weakens.
# Capacity UPDATED 2026-09-01 from an initial 14.0 ASSUMPTION to a real,
# verified spec: genuine Volvo support-battery part 32238082 (confirmed
# via usparts.volvocars.com, explicitly listed for the 2016 XC90, cross-
# corroborated by SKANDIX/FCP Euro/Superstart as a 12V 10Ah/170A AGM
# battery) — see xc90_sim/parts_catalog/electrical_drivetrain_domain.py.
SUPPORT_BATTERY_CAPACITY_AH = 10.0
SUPPORT_BATTERY_MAINTENANCE_CHARGE_W = 30.0  # smaller trickle than the main battery's — it's a buffer, not the primary source

# --- Fuse ratings (typical automotive values for these circuits; not this
# specific car's published fuse-box legend) ---
FUSE_RATING_HEADLIGHTS_A = 15.0
FUSE_RATING_WIPERS_A = 25.0
FUSE_RATING_HORN_A = 15.0
FUSE_RATING_FUEL_PUMP_A = 20.0
FUSE_RATING_COOLING_FAN_A = 40.0
FUSE_RATING_DOME_LIGHT_A = 10.0
FUSE_RATING_INFOTAINMENT_A = 15.0
FUSE_RATING_ECU_MAIN_A = 10.0

# --- Fuel pump (in-tank electric lift pump + camshaft-driven high-pressure
# pump, since this is a direct-injection engine) ---
# ASSUMPTION: none of these are published for this car; plausible values
# for this class of GDI fuel system.
LOW_PRESSURE_TARGET_BAR = 4.0
HIGH_PRESSURE_TARGET_BAR = 150.0
PRESSURE_BUILD_TIME_S = 0.6  # how long the lift pump takes to reach target on startup
MIN_OPERATING_PRESSURE_FRAC = 0.85  # below this fraction of target, fuel delivery is derated
