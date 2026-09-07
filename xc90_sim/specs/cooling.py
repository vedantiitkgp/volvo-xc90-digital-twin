"""
Cooling system — spec constants. ASSUMPTION throughout: none of these are
published for this car; plausible values for this class of turbocharged
engine's cooling system.
"""

THERMOSTAT_OPEN_TEMP_C = 90.0  # begins circulating coolant through the radiator
NORMAL_OPERATING_TEMP_C = 95.0
OVERHEAT_WARNING_TEMP_C = 115.0
FAN_ON_TEMP_C = 100.0
FAN_OFF_TEMP_C = 96.0  # a few degrees below FAN_ON to avoid rapid on/off cycling

COOLANT_THERMAL_MASS_J_PER_K = 25000.0  # coolant + engine block thermal mass this system directly affects
# Real engines send roughly a third of total fuel chemical energy to the
# coolant (the rest is useful work, exhaust heat, and radiated/friction
# losses) -- a simplification of the real energy balance (which would
# require exact instantaneous crank output power across every driveline
# branch to derive precisely), applied as one direct fraction of fuel
# energy rather than computed from a true waste-heat balance.
COOLANT_HEAT_FRACTION_OF_FUEL_ENERGY = 0.30

# Sized against this sim's own fuel-flow output, not an independent
# published number: a sustained ~100mph/half-throttle cruise burns fuel
# fast enough to send ~68kW to the coolant, and real cars don't overheat
# cruising at that speed -- so the radiator has to be able to reject
# somewhat more than that at full airflow. 90kW is a plausible rating for
# this class of turbocharged engine's radiator (the previous 25000.0 was
# roughly a third of what sustained highway cruise alone demands, which
# made coolant temp run away unbounded under any sustained load).
RADIATOR_MAX_DISSIPATION_W = 90000.0  # at full airflow (highway speed, or fan running)
RADIATOR_STATIONARY_DISSIPATION_FRAC = 0.25  # fraction of max, with no ram air, fan on
AMBIENT_HEAT_LOSS_W_PER_K = 15.0  # passive loss to ambient even with the thermostat closed

# --- Electric coolant (water) pump ---
# Real, confirmed part (see xc90_sim/parts_catalog): this engine uses an
# ELECTRIC coolant pump (genuine Volvo part 32382249), not a belt-driven
# mechanical one -- lets the ECU vary flow independently of engine rpm.
# ASSUMPTION behavior (not published): real electric-pump strategies on
# this class of engine run near-zero flow during cold start (helps the
# engine reach operating temperature faster -- less heat carried away
# from the block while it's still warming up) and ramp to full flow as
# coolant approaches operating temperature or under high load (which
# needs full cooling regardless of how warm the coolant already is).
WATER_PUMP_WARMUP_START_C = 40.0  # below this, near-zero flow
WATER_PUMP_FULL_FLOW_C = 75.0  # at or above this, full flow regardless of load
WATER_PUMP_MIN_WARMUP_FLOW_FRAC = 0.15  # never fully zero -- some circulation always needed
WATER_PUMP_RESPONSE_TAU_S = 1.0  # real pump ramps, doesn't step instantly
# After a hot shutdown, a real electric pump on a turbocharged engine
# keeps running briefly to prevent localized boiling ("heat soak") around
# the turbo -- ASSUMPTION duration/threshold.
WATER_PUMP_POST_SHUTDOWN_RUN_S = 60.0
WATER_PUMP_POST_SHUTDOWN_MIN_TEMP_C = 100.0  # only runs post-shutdown if coolant was this hot
