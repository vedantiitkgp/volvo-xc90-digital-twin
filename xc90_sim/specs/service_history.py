"""
Real service history for this specific car (VIN YV4A22PKXG1092057), from the
owner's CARFAX report. This is the single source of truth the wear model
reads from — to reflect a new real-world service event (a repair, a
replacement, an oil change), just append a new ServiceEvent here. Nothing
else needs to change; xc90_sim.wear.WearModel recomputes each component's
condition from whatever the latest matching event is.

`component` values must match a key in xc90_sim.wear.wear_model.WEARABLE_COMPONENTS.
"""

from collections import namedtuple

ServiceEvent = namedtuple("ServiceEvent", ["date", "mileage", "component", "action"])

# date, mileage, component, action ("replaced" resets wear to new; "serviced" is
# informational only and doesn't reset wear unless noted).
HISTORY = [
    ServiceEvent("2016-04-15", 0, "manufactured", "vehicle manufactured"),
    ServiceEvent("2017-07-05", 10135, "engine_general", "turbocharger replaced/repaired"),
    ServiceEvent("2017-07-25", 12741, "rear_brakes", "rear brake rotor(s) replaced"),
    ServiceEvent("2017-10-21", 12741, "tires", "tires replaced"),
    ServiceEvent("2019-01-10", 25078, "tires", "tires replaced"),
    ServiceEvent("2020-08-28", 43745, "rear_brakes", "rear brake pads replaced"),
    ServiceEvent("2020-10-27", 45458, "rear_brakes", "rear brake pads/shoes replaced"),
    ServiceEvent("2021-03-17", None, "body", "minor front-end accident damage"),
    ServiceEvent("2021-12-23", 59860, "tires", "tires replaced"),
    ServiceEvent("2023-11-28", 83216, "front_brakes", "front brake pads/rotors replaced"),
    ServiceEvent("2023-11-28", 83216, "rear_brakes", "rear brake pads/rotors replaced"),
    ServiceEvent("2024-08-13", 92228, "engine_mounts", "engine mount(s) replaced"),
    ServiceEvent("2025-04-19", 105021, "rear_brakes", "rear brake pads/rotors replaced"),
]

# Most recent known odometer reading (also in specs.vehicle_identity) — the
# default "current mileage" the wear model evaluates each component at.
CURRENT_MILEAGE = 115367
CURRENT_DATE = "2026-01-28"
