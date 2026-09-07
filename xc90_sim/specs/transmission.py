"""
Aisin TG-81SC 8-speed automatic (marketed as AWF8F45; badge-engineered
across many OEMs -- also EAT8 at PSA, GA8F22AW at BMW/Mini, AF50-8 at
Opel/Vauxhall, AQ450 at VW Group) -- spec constants.

Corrected 2026-08-19: this project previously called it "AW8G30," which
research turned up no evidence for -- OEM eBay listings ("2016-2022 VOLVO
XC90 2.0L AWD T6 AW TG81SC"), SwedeSpeed threads, and gearboxlist.com/
remanglobal.com's cross-reference of the shared Aisin platform all confirm
TG-81SC as the real Volvo-specific designation. Gear ratios below are NOT
re-derived from this correction -- they were already treated as sourced
from Volvo's own published spec sheet (not flagged ASSUMPTION), and a
different OEM's application of the same shared transmission (e.g. a Lexus
RX350 using 5.250/3.028/.../0.673) has a different ratio spread by design,
so it isn't evidence these are wrong -- just not independently re-verified.
"""

GEAR_RATIOS = {
    1: 4.714,
    2: 3.143,
    3: 2.106,
    4: 1.667,
    5: 1.285,
    6: 1.000,
    7: 0.839,
    8: 0.667,
}
REVERSE_RATIO = 3.295
FINAL_DRIVE_RATIO = 3.727

# Torque converter, modeled with the standard two characteristic curves:
#   - torque ratio: how much the turbine torque is multiplied vs. pump torque
#   - capacity factor: how much torque the pump absorbs from the engine at a
#     given pump speed, independent of what the engine is trying to produce
# ASSUMPTION: typical passenger-car converter shape, lockup above 0.90 SR.
CONVERTER_SPEED_RATIO = [0.0, 0.2, 0.4, 0.6, 0.8, 0.9, 1.0]
CONVERTER_TORQUE_MULTIPLIER = [2.2, 1.9, 1.55, 1.25, 1.05, 1.0, 1.0]
CONVERTER_LOCKUP_SPEED_RATIO = 0.90
# ASSUMPTION: capacity factor Nm/(rad/s)^2, tuned so a stall (SR=0) against
# full engine torque (400 Nm) settles around ~2900 rpm, typical for this class.
# Checked 2026-08-19: no usable stall-speed datalog/dyno/forum figure found
# for this specific TG-81SC+Drive-E-T6 combo — the relevant SwedeSpeed
# threads are now paywalled (tollbit.swedespeed.com, HTTP 402) and
# archive.org is unreachable from this environment. Generic figures exist
# for a different, older Volvo drivetrain (turbo-only T6 + TF-80SC, ~2000-
# 2800 rpm) but aren't evidence for this one. Remains an unverified guess.
CONVERTER_CAPACITY_FACTOR = 0.0044

# --- Transmission cooler ---
# Real named part (reified out of TransmissionFluid's previous bare
# per-Kelvin dissipation constant): most passenger-car transmission
# coolers are small air-cooled heat exchangers with no fan of their own
# (unlike the engine radiator), so effectiveness genuinely depends on
# vehicle speed (ram air) with only a small natural-convection floor at a
# dead stop. ASSUMPTION values -- not published for this car.
TRANS_COOLER_MIN_DISSIPATION_W_PER_K = 10.0  # natural convection at a dead stop
TRANS_COOLER_MAX_DISSIPATION_W_PER_K = 55.0  # at full ram-air speed
TRANS_COOLER_RAM_AIR_SATURATION_MPS = 30.0  # same saturation speed as the engine radiator
