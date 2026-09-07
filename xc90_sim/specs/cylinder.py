"""
Cylinder-level combustion geometry and thermodynamics — spec constants for
a genuine (if single-zone-simplified) 4-stroke combustion model, replacing
the empirical torque-curve lookup engine.py used to use internally (same
public Engine interface, real physics underneath now).

Real, verified numbers (checked 2026-08-22, not guessed): bore 82.0mm /
stroke 93.2mm for the Drive-E B4204T9 twincharger (self-consistent with
this project's already-published 1.969L displacement and 4 cylinders:
4 * pi/4 * 0.082^2 * 0.0932 = 1.969L, matches exactly) — via mymotorlist.com's
Volvo B4204T9 spec page. Timing BELT (not chain) confirmed via multiple
independent forum/tech sources, real 150,000mi/12yr replacement interval —
see wear/wear_model.py's timing_belt entry.

Genuinely ASSUMPTION (proprietary/unpublished, flagged individually below):
connecting rod length, exact cam profile/valve timing, Wiebe combustion
shape parameters, volumetric efficiency curve, boost/twincharger maps,
target air-fuel ratio schedule.
"""

import math

from . import engine as _engine

CYLINDER_COUNT = 4
# Firing order 1-3-4-2 is the standard inline-4 pattern and is what's
# commonly cited for this engine family — but note it doesn't actually
# change any physics in this single-zone-per-cylinder model (see
# engine/cylinder.py): every cylinder is identical and 180 degrees
# apart regardless of which physical cylinder number gets which phase, so
# this is a labeling detail, not something worth independently verifying.
FIRING_ORDER = (1, 3, 4, 2)

BORE_M = 0.0820  # published (Volvo B4204T9), verified self-consistent with displacement above
STROKE_M = 0.0932  # published, same source
CRANK_RADIUS_M = STROKE_M / 2.0  # exact geometric identity, not a separate assumption
# ASSUMPTION: connecting rod length isn't published for this engine; 1.75x
# crank radius is a typical rod ratio for this class of high-revving turbo engine.
CONNECTING_ROD_LENGTH_M = CRANK_RADIUS_M * 1.75

_BORE_AREA_M2 = math.pi / 4.0 * BORE_M ** 2
_DISPLACED_VOLUME_PER_CYL_M3 = _BORE_AREA_M2 * STROKE_M
# Clearance volume derived from the REAL published compression ratio +
# displacement, not independently guessed: CR = (Vd + Vc) / Vc.
CLEARANCE_VOLUME_M3 = _DISPLACED_VOLUME_PER_CYL_M3 / (_engine.COMPRESSION_RATIO - 1.0)

# --- Valve timing (crank-angle degrees, this cylinder's own 0-720 cycle) ---
# ASSUMPTION: exact cam profile is proprietary; typical values for this
# class of DOHC turbo engine with some intake/exhaust overlap at TDC.
INTAKE_OPEN_DEG_BTDC = 15.0    # opens before TDC (the overlap period)
INTAKE_CLOSE_DEG_ABDC = 50.0   # closes well after BDC (real engines trap charge late)
EXHAUST_OPEN_DEG_BBDC = 45.0   # opens before BDC of the power stroke (blowdown)
EXHAUST_CLOSE_DEG_ATDC = 15.0  # closes after TDC (matching the intake-open overlap)

# --- Valve lift (real DOHC 4-valve-per-cylinder: 2 intake + 2 exhaust) ---
# ASSUMPTION: exact lift curve is proprietary; a smooth raised-cosine-style
# profile (rises from 0 at open, peaks at mid-duration, back to 0 at
# close) is the standard simplified shape used when the real cam profile
# isn't available -- not a fabricated behavior, a real curve family.
INTAKE_VALVES_PER_CYLINDER = 2
EXHAUST_VALVES_PER_CYLINDER = 2
MAX_INTAKE_LIFT_MM = 9.5   # ASSUMPTION: typical for this class of engine
MAX_EXHAUST_LIFT_MM = 9.0  # ASSUMPTION

# --- Fuel injector (direct injection -- this engine is a GDI design) ---
# ASSUMPTION: real injector flow rating isn't published; sized so the
# resulting pulse widths land in the realistic few-ms range this class of
# injector actually operates in, not an arbitrary number.
INJECTOR_FLOW_RATE_KG_PER_S = 0.012  # ASSUMPTION
INJECTOR_MAX_PULSE_WIDTH_MS = 25.0  # physical ceiling: can't stay open longer than this

# --- Combustion: single-zone Wiebe heat-release model ---
# The standard simplified (not CFD/multi-zone) technique for in-cylinder
# combustion modeling. ASSUMPTION shape parameters -- these are standard
# generic textbook values, not measurements of this specific engine's burn.
WIEBE_EFFICIENCY_FACTOR = 6.9  # "a" parameter
WIEBE_SHAPE_M = 2.0            # "m" parameter
COMBUSTION_DURATION_DEG = 50.0  # crank-angle duration of the burn
SPARK_ADVANCE_DEG_BTDC = 15.0   # ASSUMPTION: typical spark timing at cruise load
COMBUSTION_EFFICIENCY = 0.97    # ASSUMPTION: fraction of fuel energy actually released (not 100%, real engines have some incomplete combustion)

# --- Working fluid / fuel properties (real published constants, not this-engine-specific) ---
FUEL_LHV_J_PER_KG = 44.0e6      # gasoline lower heating value
STOICHIOMETRIC_AFR = 14.7       # real constant for gasoline
COMBUSTION_GAMMA = 1.30         # ratio of specific heats for hot combustion products (real approx, < air's 1.4)
INTAKE_GAMMA = 1.35             # polytropic exponent during compression (real gas + heat transfer, < adiabatic 1.4)
# ASSUMPTION: recirculated exhaust gas (EGR + PCV blow-by) is mostly
# triatomic CO2/H2O, which has more internal degrees of freedom and a
# lower specific-heat ratio than diatomic-dominated fresh air (~1.15-1.30
# for hot exhaust products vs air's 1.4) -- a diluted intake charge's
# effective gamma during compression is blended toward this floor in
# proportion to dilution fraction (see Cylinder.step()'s dilution_frac),
# the real second mechanism (beyond simple fresh-charge displacement,
# already modeled as a VE derate) by which EGR/PCV affect the compression
# and combustion pressure trace -- still a single blended-gamma
# approximation, not a full multi-species thermodynamic simulation.
DILUTED_CHARGE_GAMMA_MIN = 1.30
SPECIFIC_GAS_CONSTANT_J_PER_KGK = 287.0  # air, real constant
INTAKE_CHARGE_TEMP_K = 320.0    # ASSUMPTION: post-intercooler charge temp, typical for a boosted engine

# --- Volumetric efficiency ---
# ASSUMPTION: no published VE curve for this engine; a plausible
# rpm-dependent shape (rises from idle, peaks in the midrange where the
# intake/exhaust tuning is optimized, tapers at very high rpm) typical for
# a turbocharged/supercharged 4-cylinder.
VE_RPM_POINTS = [800, 2000, 4000, 5700, 6200]
VE_FRACTION_POINTS = [0.75, 0.88, 0.95, 0.92, 0.85]

# --- Twincharger boost model ---
# Researched 2026-08-18/19 (see specs/awd.py's Haldex research for the
# unrelated AWD side of that pass, and STATUS.md): real forum/press
# sources describe the supercharger covering idle to ~1600rpm, the turbo
# beginning to spool by ~3500rpm, and the supercharger's electromagnetic
# clutch disengaging around 3500-3800rpm -- corroborated across
# independent sources (moderate confidence), used directly here rather
# than guessed from scratch.
SUPERCHARGER_DISENGAGE_RPM = 3650.0  # midpoint of the researched 3500-3800rpm range
SUPERCHARGER_FULL_BOOST_RPM = 1600.0  # researched: covers idle to ~1600rpm at full boost
TURBO_SPOOL_START_RPM = 3500.0        # researched: turbo begins spooling ~3500rpm
TURBO_FULL_BOOST_RPM = 5200.0  # ASSUMPTION: not independently researched; plausible for full turbo boost to build in
# ASSUMPTION: neither peak boost figure is published for this exact engine.
# Calibrated (2026-08-22) against the published ~400Nm flat torque
# plateau (2200-5400rpm) and 316hp@5700rpm peak power: a real ECU targets
# a boost profile that HOLDS torque flat despite the turbo having more
# boost "available" at higher rpm than the supercharger provides lower
# down (wastegate/bypass control) -- these two are deliberately close in
# magnitude to reproduce that flat plateau, not "whatever the turbo can
# do" at each rpm.
SUPERCHARGER_MAX_BOOST_PA = 0.68e5   # ~0.68 bar / ~9.9 psi
TURBO_MAX_BOOST_PA = 0.70e5          # ~0.70 bar / ~10.2 psi
ATMOSPHERIC_PRESSURE_PA = 101325.0

# --- Target air-fuel ratio schedule ---
# ASSUMPTION: real ECU AFR maps are proprietary; the *shape* (stoichiometric
# at low load, richening under boost for cooling/knock protection) is real,
# well-documented tuning practice, not a fabricated behavior.
AFR_AT_NO_BOOST = STOICHIOMETRIC_AFR
AFR_AT_FULL_BOOST = 12.3  # ASSUMPTION: typical WOT-under-boost enrichment target

# --- Throttle -> effective manifold pressure ---
# ASSUMPTION: real throttle-plate flow restriction isn't separately
# simulated (would need 1D gas dynamics); this composite model instead has
# throttle position directly modulate manifold pressure between idle
# vacuum and full atmospheric+boost -- captures the real qualitative
# behavior (closed throttle = vacuum/pumping loss, wide open = full boost)
# without a full flow-restriction simulation.
IDLE_MAP_FRACTION = 0.30  # ASSUMPTION: typical idle manifold vacuum, ~30% of atmospheric absolute
# A real Idle Air Control valve/electronic throttle maintains a minimum
# airflow independent of pedal position specifically to keep idle stable
# against friction/accessory loads -- modeling this real, named system
# rather than an ad hoc "idle assist" torque fudge.
IDLE_AIR_CONTROL_MIN_THROTTLE_FRAC = 0.10  # ASSUMPTION

# --- Numerical sub-stepping ---
# Combustion physics happens on a much faster timescale (a full 4-stroke
# cycle at redline can be a full crank revolution or more within a single
# outer Simulation dt) than the outer vehicle-dynamics loop steps at, so
# the engine sub-steps internally rather than using the outer dt directly
# -- otherwise a single Euler step could alias right past an entire
# combustion event (the burn only spans ~50 crank-degrees). The substep
# COUNT is chosen adaptively each call to keep degrees-per-substep at or
# below this target, rather than a fixed count -- a fixed count that's
# fine enough at a small outer dt (e.g. 500Hz launch studies) is far too
# coarse at a larger one (e.g. 50Hz trip logging), which genuinely
# destabilized the pressure ODE (large Euler steps through a stiff
# combustion process oscillate rather than converge) until this was
# caught by testing a sustained partial-throttle cruise, not just a
# full-throttle launch.
MAX_CRANK_DEG_PER_SUBSTEP = 5.0
MAX_CRANK_SUBSTEPS_PER_TICK = 300  # cost ceiling for extreme rpm*dt combinations

# --- PCV (Positive Crankcase Ventilation) ---
# Real, federally-mandated emissions system on every gasoline car since the
# 1960s: routes blow-by gas (combustion gas that leaks past the piston
# rings into the crankcase) back into the intake to be burned, rather than
# vented to atmosphere. ASSUMPTION magnitudes (not published for this
# engine): real blow-by on a healthy engine is a small fraction of intake
# flow, well under EGR's -- both derate volumetric efficiency the same way
# (recirculated gas displaces fresh air), but PCV's effect is an order of
# magnitude smaller.
PCV_BASE_BLOWBY_FRACTION = 0.003  # fresh-engine baseline, fraction of intake flow
PCV_MAX_WEAR_BLOWBY_INCREASE_FRAC = 2.0  # a heavily worn engine can blow by several times more
