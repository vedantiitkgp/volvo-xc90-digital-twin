"""
Exhaust system — spec constants. ASSUMPTION throughout: none of these are
published for this car; plausible values for this class of turbocharged
engine's exhaust system.
"""

# --- Catalytic converter ---
# Real, well-known behavior: a cold catalytic converter doesn't convert
# pollutants effectively until it reaches its "light-off" temperature —
# real reason cold-start emissions are worse than warmed-up emissions.
CATALYST_LIGHT_OFF_TEMP_C = 300.0
CATALYST_HEATUP_TAU_S = 20.0  # small ceramic substrate -- heats up fast once exhaust flows
EXHAUST_GAS_TEMP_C = 650.0  # ASSUMPTION: typical EGT under load for this class of turbo engine
AMBIENT_TEMP_C = 20.0  # what the catalyst cools toward with the engine off

# --- Exhaust backpressure ---
# Real: the catalytic converter + muffler restrict exhaust flow, creating
# backpressure the engine has to push against during the exhaust stroke —
# a genuine (if usually small) pumping loss. ASSUMPTION magnitude.
BACKPRESSURE_PA = 8000.0  # ~0.08 bar

# --- Oxygen (O2 / lambda) sensor ---
# Real, standard closed-loop AFR feedback sensor. ASSUMPTION noise/response.
O2_SENSOR_NOISE_STD_LAMBDA = 0.01
O2_SENSOR_RESPONSE_TAU_S = 0.15  # real O2 sensors aren't instant

# --- EGR (Exhaust Gas Recirculation) ---
# Real emissions-control system: recirculates a small fraction of exhaust
# into the intake to reduce peak combustion temperature (lowers NOx).
# ASSUMPTION: exact flow map is proprietary; a plausible max flow fraction
# and the real qualitative behavior (more EGR at light/mid load & cruise
# rpm, none at idle or high load, where it would hurt driveability/power).
EGR_MAX_FLOW_FRACTION = 0.12
EGR_MIN_RPM = 1200.0
EGR_MAX_RPM = 3500.0
