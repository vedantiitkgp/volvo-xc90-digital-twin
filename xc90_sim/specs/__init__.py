"""
Vehicle spec constants, grouped by subsystem module (engine, transmission,
awd, chassis). Import the submodule you need directly, e.g.:

    from xc90_sim.specs import engine as engine_specs
"""

from . import engine, transmission, awd, chassis, suspension, steering, tire, dsc, vehicle_identity
from . import linkage, sensors, body, cabin, cylinder, fuel, accessories

__all__ = [
    "engine", "transmission", "awd", "chassis", "suspension", "steering", "tire", "dsc", "vehicle_identity",
    "linkage", "sensors", "body", "cabin", "cylinder", "fuel", "accessories",
]
