"""2016 XC90 T6 AWD Momentum — chassis/body spec constants."""

CURB_MASS_KG = 1935  # published spec, T6 AWD Momentum (4,394 lb)
DRAG_COEFFICIENT = 0.32
FRONTAL_AREA_M2 = 2.81
WHEELBASE_M = 2.984
TIRE_ROLLING_RADIUS_M = 0.3706  # 235/55R19, confirmed by owner as this car's actual wheel/tire size
ROLLING_RESISTANCE_COEFFICIENT = 0.0085  # researched 2026-08-19: no source
# confirms which of the three real "VOL"-sidewall-marked OE tires (Pirelli
# Scorpion Verde, Michelin Latitude Tour HP N0, Continental CrossContact LX
# Sport) is on this specific VIN, but EU tire-label EPREL fiches for close
# sizes of these models all land in Class B/C (0.0066-0.0090 range per EU
# Reg. 2020/740) -- the previous 0.011 sits at/above Class E, the *worst*
# class, which is inconsistent with any plausible OEM touring-tire candidate
# found. Still an ASSUMPTION (no exact-size 235/55R19 fiche located) but now
# bounded by real label data instead of an unaudited guess.

TIRE_FRICTION_COEFFICIENT = 0.82  # calibrated: Car and Driver's real skidpad test
# of a 2016 XC90 T6 AWD Inscription measured 0.81g; this sim's own peak sustained
# cornering g (a proper full-lock sweep, not just a moderate-steer sample) came out
# to 0.89g before this adjustment. Inscription's tested car may have had different
# (larger/grippier) optional wheels than this Momentum's confirmed 235/55R19, so
# treat this as the best available real reference, not an exact match.
WHEEL_INERTIA_KGM2 = 2.58  # derived, not guessed: typical 235/55R19 tire (~27 lb) +
# typical 19" alloy wheel (~26-29 lb) = ~24.7 kg, at an effective radius of gyration
# ~0.85x rolling radius (standard approximation — most mass is at the rim/tread, not
# the hub) = 2.45 kg*m^2, plus an ASSUMPTION ~10kg/0.16m brake rotor (disk, 0.5*m*r^2)
# = 0.13 kg*m^2. Not this exact OEM wheel's published weight (unavailable), but a real
# tire/wheel-class weight instead of an arbitrary round number.
MAX_BRAKE_DECEL_G = 1.0  # calibrated: Car and Driver's 70-0mph brake test (161 ft) on
# the same Inscription implies ~1.0g average deceleration; this sim's own 70-0 stop
# came out to 186 ft (~16% longer) before further tuning — the gap is most likely
# ABS's conservative release fraction eating into ideal deceleration during the stop.
BRAKE_FRONT_BIAS = 0.65  # ASSUMPTION: typical front-biased brake proportioning.
# Checked 2026-08-19: genuine Volvo OEM rotor sizes for the standard-brake
# T6 (part 30657301 front = 336mm, parts 31471816/31400778 rear = 320mm)
# confirm the *direction* (front rotor is larger, consistent with front
# bias) but a 336/320 diameter ratio (~1.05, ~1.10 swept-area) is far too
# small to derive an exact force-split percentage -- rotor size reflects
# thermal/torque capacity, not the hydraulic proportioning valve's bias,
# which Volvo doesn't publish. No brake-dyno source with a measured bias
# percentage was found. Stays an ASSUMPTION, now direction-corroborated.

AIR_DENSITY_KGM3 = 1.225
GRAVITY_MS2 = 9.80665

# --- Brake booster vacuum system ---
# Real, confirmed reason this exists on this engine: independent variable
# valve timing on both camshafts leaves too little manifold vacuum at low
# rpm for the brake booster, so this car uses a small ELECTRIC vacuum pump
# (genuine Volvo part, e.g. 31401152) switched on by a vacuum switch when
# the reservoir runs low and off once restored — not a continuously-running
# mechanical pump (checked 2026-08-24: forum/parts-catalog sources confirm
# the electric pump + vacuum-switch behavior for this engine family; exact
# reservoir capacity/pump flow rate/switch thresholds aren't published, so
# those numbers below are ASSUMPTION, plausible for this class of system).
VACUUM_RESERVOIR_FULL_KPA = 65.0  # kPa below atmospheric, reservoir at full charge
VACUUM_MIN_FOR_FULL_ASSIST_KPA = 45.0  # below this, boost assist starts tapering
VACUUM_PUMP_ON_KPA = 35.0  # pump switches on once vacuum drops to this
VACUUM_PUMP_OFF_KPA = 60.0  # pump switches off once vacuum is restored to this (hysteresis)
VACUUM_CONSUMPTION_KPA_PER_S = 8.0  # at full brake pedal — braking is what draws the reservoir down
VACUUM_PUMP_BUILD_KPA_PER_S = 15.0  # real electric pumps run in short bursts, not continuously
# ASSUMPTION: a real car with zero booster assist is still drivable (much
# harder to stop, not undrivable) — floor braking effectiveness rather
# than letting it go to zero.
UNBOOSTED_BRAKE_FRACTION = 0.35
