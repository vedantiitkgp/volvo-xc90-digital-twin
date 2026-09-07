"""Wheel speed sensor characteristics — spec constants."""

# Real wheel speed sensors (variable-reluctance/Hall-effect) count pulses off
# a toothed reluctor ring; speed is quantized to whole pulses per sample
# window, which is why they're notoriously imprecise at very low speed —
# few pulses occur in a short window at low omega.
# Confirmed 2026-08-19: genuine Volvo tone-ring part 30735955 and a
# third-party ("Tenaci") reluctor product both independently list 48 teeth
# for this platform. Front/rear equivalence isn't separately confirmed (one
# SwedeSpeed thread shows owners themselves unsure), and neither source is
# SPA-platform(2015+)-specific vs. carryover from the older P2 XC90 — but
# 48 is now a corroborated real part spec, not a bare guess.
WHEEL_SPEED_SENSOR_PULSES_PER_REV = 48
WHEEL_SPEED_SENSOR_NOISE_STD_RAD_S = 0.05  # small measurement/electrical noise, still ASSUMPTION

# --- GPS receiver (real, well-documented civilian GPS characteristics) ---
EARTH_RADIUS_M = 6371000.0  # real, standard mean Earth radius
GPS_POSITION_NOISE_STD_M = 3.0  # real, typical consumer/automotive GPS accuracy (a few meters CEP)
