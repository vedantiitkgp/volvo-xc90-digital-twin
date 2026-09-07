"""
Identity of the specific real car this simulation models — pure metadata,
no physics. Confirmed from the owner's CARFAX report and window sticker.

Wear/condition from the CARFAX service history (turbo replaced at 10,135 mi,
several brake jobs, one minor front-end accident in 2021, 115k+ miles) is
NOT modeled here — that's a separate future task (a mileage/wear-driven
degradation model), not identity. This module is snapshot metadata only.
"""

VIN = "YV4A22PKXG1092057"
MODEL_YEAR = 2016
TRIM = "T6 Momentum"
DRIVETRAIN = "AWD"
ENGINE_DESCRIPTION = "2.0L I4 DOHC 16V, turbocharged + supercharged (Drive-E)"
BODY_STYLE = "4-door wagon/sport utility"

# Snapshot from the owner's CARFAX report, not live-updated by this sim.
ODOMETER_SNAPSHOT_MI = 115367
ODOMETER_SNAPSHOT_DATE = "2026-01-28"
