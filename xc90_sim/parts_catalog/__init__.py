"""
Real Volvo OEM parts catalog for this specific 2016 XC90 T6 Momentum AWD
(VIN YV4A22PKXG1092057) simulation. Maps every simulated component class
to the REAL physical part(s) it represents, with a genuine, source-
verified OEM part number where one could be confirmed via web research --
or an honest "NOT_FOUND" where it couldn't (a pure-software/logic class
with no hardware of its own, a part that doesn't have its own discrete
Volvo-catalog number, or a real search that didn't turn up a confirmed
match for this exact car/generation).

See README.md in this directory for the full schema and research method.
The short version: every "oem_part_number" here is either a real number
with a source_url, exactly the string "NOT_FOUND" (a real search that
didn't turn up a confirmed match), or exactly the string "NOT_APPLICABLE"
(the real part doesn't exist for this component at all -- e.g. this
engine's EGRValve models a real internal-EGR effect that has no discrete
external valve on this specific engine) -- never a plausible-looking
guess. Several numbers carry a "notes" caveat where fitment to this exact
VIN/model-year couldn't be fully pinned down even though a real part
number was found -- read the notes, not just the number.

Researched 2026-08-31/09-01 across 5 domains (engine/fuel/exhaust/cooling,
electrical/drivetrain, transmission/chassis/suspension/steering, body/DSC,
cabin electronics), covering all ~70 classes simulated at that time.
"""

from .engine_domain import PARTS as _ENGINE_PARTS
from .electrical_drivetrain_domain import PARTS as _ELECTRICAL_DRIVETRAIN_PARTS
from .transmission_chassis_domain import PARTS as _TRANSMISSION_CHASSIS_PARTS
from .body_dsc_domain import PARTS as _BODY_DSC_PARTS
from .cabin_domain import PARTS as _CABIN_PARTS

PARTS_CATALOG = {}
for _domain in (
    _ENGINE_PARTS, _ELECTRICAL_DRIVETRAIN_PARTS, _TRANSMISSION_CHASSIS_PARTS,
    _BODY_DSC_PARTS, _CABIN_PARTS,
):
    PARTS_CATALOG.update(_domain)


def lookup(sim_class_name):
    """Real part(s) for a simulated class, by its bare class name (e.g. "Alternator")."""
    return PARTS_CATALOG.get(sim_class_name)


def verified_part_number(sim_class_name, part_name=None):
    """Convenience: the first (or name-matching) verified OEM part number
    for a class, or None if not found/not verified. part_name disambiguates
    classes with multiple real_parts entries (e.g. "Battery" -> main vs.
    support, "WheelBearing" -> front vs. rear)."""
    entry = PARTS_CATALOG.get(sim_class_name)
    if not entry:
        return None
    for rp in entry["real_parts"]:
        if part_name is not None and rp["name"] != part_name:
            continue
        if rp["oem_part_number"] not in (None, "NOT_FOUND", "NOT_APPLICABLE"):
            return rp["oem_part_number"]
    return None


def summary():
    """Coverage stats across the whole catalog."""
    total_entries = 0
    verified = 0
    for entry in PARTS_CATALOG.values():
        for rp in entry["real_parts"]:
            total_entries += 1
            if rp["oem_part_number"] not in (None, "NOT_FOUND", "NOT_APPLICABLE"):
                verified += 1
    return {
        "sim_classes_covered": len(PARTS_CATALOG),
        "real_parts_entries": total_entries,
        "verified": verified,
        "not_found": total_entries - verified,
    }
