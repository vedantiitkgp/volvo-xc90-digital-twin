"""
Drive-E 2.0L I4, turbocharged + supercharged ("Twincharger") — spec constants.

Sourced from Volvo published spec sheets / press materials for the 2016 XC90
T6. Values the public spec sheet doesn't give (crank inertia, friction,
boost-response time constant) are plausible estimates for an engine of this
class, flagged ASSUMPTION.
"""

DISPLACEMENT_L = 1.969
CYLINDERS = 4
COMPRESSION_RATIO = 10.3
IDLE_RPM = 800
REDLINE_RPM = 6200
PEAK_POWER_HP = 316
PEAK_POWER_RPM = 5700
PEAK_TORQUE_NM = 400  # 295 lb-ft
PEAK_TORQUE_RPM_LOW = 2200
PEAK_TORQUE_RPM_HIGH = 5400

# Torque curve control points (rpm -> Nm at full throttle / full boost),
# shaped so peak power lands at ~316 hp @ 5700 rpm to match spec.
TORQUE_CURVE_RPM = [
    IDLE_RPM, 1000, 1500, 2000,
    PEAK_TORQUE_RPM_LOW, 3000, 4000, PEAK_TORQUE_RPM_HIGH,
    5700, 6000, REDLINE_RPM,
]
TORQUE_CURVE_NM = [
    150, 220, 340, 390,
    400, 400, 400, 400,
    396, 350, 0,
]

# ASSUMPTION: neither is published; plausible values for this class of car's starter/ignition.
STARTER_CRANK_TIME_S = 0.8
MIN_BRAKE_FRAC_TO_START = 0.05

# Belt-driven accessory load moved to a real Alternator/AccessoryBelt/
# FuelPump-based calculation (see engine/engine.py's
# _accessory_load_torque_nm and specs/accessories.py) that responds to
# actual electrical demand (headlights, HVAC fan, seat heaters, etc.)
# instead of one flat constant.

# Engine Auto Start/Stop: shuts the engine off at a stop to save fuel, then
# restarts automatically -- NOT the same as turning the ignition off
# (accessories/ignition stay fully on throughout). ASSUMPTION: none of
# these thresholds are published; plausible values for this class of
# feature. Restart is much faster than a cold start-up (a real auto-stop
# system uses an enhanced starter/integrated starter-generator) -- modeled
# as a short crank rather than instant, same technique as STARTER_CRANK_TIME_S.
AUTO_STOP_RESTART_TIME_S = 0.3
AUTO_STOP_MAX_SPEED_MPS = 0.5  # only engages once essentially stopped
AUTO_STOP_MIN_BRAKE_FRAC_TO_ENGAGE = 0.3
AUTO_STOP_RESUME_BRAKE_FRAC = 0.15  # releasing the brake below this resumes the engine

# Flywheel, decomposed out as a real named component (see
# engine/flywheel.py) rather than folded invisibly into one crank
# inertia number. FLYWHEEL_INERTIA_KGM2 is DERIVED (I = 0.5*m*r^2 for a
# solid disc), not guessed, from an ASSUMPTION mass/radius plausible for
# this class of engine (real teardown numbers aren't published).
FLYWHEEL_MASS_KG = 7.5  # ASSUMPTION
FLYWHEEL_RADIUS_M = 0.13  # ASSUMPTION
FLYWHEEL_INERTIA_KGM2 = 0.5 * FLYWHEEL_MASS_KG * FLYWHEEL_RADIUS_M ** 2

# The remainder of the original lumped CRANK_INERTIA_KGM2 ASSUMPTION
# (crank pins/rod big-ends/pulleys/harmonic damper) that isn't the
# flywheel itself. Kept so CRANK_INERTIA_KGM2's total value (below) stays
# exactly what it was already calibrated against (see engine.py's
# wide_open_torque_nm() calibration against the published torque curve) --
# this decomposition adds real component-level detail without silently
# changing the physics.
OTHER_ROTATING_INERTIA_KGM2 = 0.15 - FLYWHEEL_INERTIA_KGM2

CRANK_INERTIA_KGM2 = FLYWHEEL_INERTIA_KGM2 + OTHER_ROTATING_INERTIA_KGM2  # == 0.15, see above
# Checked 2026-08-19: no Volvo Drive-E SAE paper, patent, or teardown with
# rotating-assembly mass/inertia data was found. Total remains an
# unverified guess; the flywheel/other split above is new (2026-08-23),
# also unverified, but now attributes the guess to real named parts.
BOOST_LAG_TAU_S = 0.15  # ASSUMPTION: twincharging removes most classic turbo lag.
# Checked 2026-08-19: several independent write-ups (SwedeSpeed/AutoGuide,
# Go-Parts, mechanic.com.au technical guides) consistently describe the
# handoff in RPM terms, not seconds — supercharger alone covers idle to
# ~1600 rpm, turbo begins spooling ~3500 rpm, supercharger clutch disengages
# ~3500-3800 rpm — corroborated across sources (moderate confidence) but
# these are engineering-journalism paraphrase, not a Volvo primary document,
# and none give an actual time-based spool curve. The 0.15s tau itself is
# still not directly sourced — this is context, not a replacement number.
