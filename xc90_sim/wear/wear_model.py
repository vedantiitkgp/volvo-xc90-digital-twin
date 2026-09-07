"""
Generic mileage-based wear model: for each wearable component, finds the
mileage at its most recent "replaced" service event (or 0, if it's never
been replaced — it's been wearing since new), and linearly degrades a
condition fraction from 1.0 (fresh) toward a floor value over a typical
service life. To reflect a new real-world repair, append a ServiceEvent to
specs/service_history.py — nothing here needs to change.

This deliberately stays a linear, single-number-per-component model (not a
detailed physical wear mechanism per part) — consistent with this project's
established pattern of flagged ASSUMPTION approximations elsewhere. What it
buys over hardcoding "the car is new": the sim reflects *this specific car's*
actual wear state at its actual current mileage, and updates automatically
as new service events are appended.
"""

from collections import namedtuple
from datetime import date

from ..specs import service_history

WearableComponent = namedtuple("WearableComponent", ["typical_life_miles", "floor_condition"])
# Some real components wear out with calendar age/charge-cycling more than
# mileage (a 12V battery is the clear case here) -- a separate, parallel
# age-based model rather than forcing everything through the mileage-based
# one above.
AgeWearableComponent = namedtuple("AgeWearableComponent", ["typical_life_days", "floor_condition"])

# ASSUMPTION values (typical component service life / how degraded a fully-
# worn example still performs) — not measurements of these specific parts.
WEARABLE_COMPONENTS = {
    "tires": WearableComponent(typical_life_miles=50000, floor_condition=0.75),
    "front_brakes": WearableComponent(typical_life_miles=45000, floor_condition=0.80),
    "rear_brakes": WearableComponent(typical_life_miles=45000, floor_condition=0.80),
    "engine_general": WearableComponent(typical_life_miles=200000, floor_condition=0.95),
    "suspension_bushings": WearableComponent(typical_life_miles=150000, floor_condition=0.90),
    # Real, published interval (checked 2026-08-22, multiple independent
    # sources): the Drive-E B4204 uses a timing BELT (not chain),
    # replacement due at 150,000mi/12yr. floor_condition=1.0 deliberately
    # -- a timing belt doesn't gradually degrade performance the way tires/
    # brakes do, it's fine until it isn't (a snapped belt is catastrophic,
    # not a gradual falloff), so this entry exists purely for maintenance-
    # due tracking (see service_due()), not to scale any physics.
    "timing_belt": WearableComponent(typical_life_miles=150000, floor_condition=1.0),
    # ASSUMPTION: this specific car's accessory/serpentine belt interval
    # isn't documented in service_history.py; a commonly-cited interval
    # for this class of belt. Same floor_condition=1.0 reasoning as above.
    "accessory_belt": WearableComponent(typical_life_miles=90000, floor_condition=1.0),
    # Wheel bearings: real, gradual wear (unlike the belts above) -- a
    # fully-worn bearing adds a modest amount of rolling resistance (see
    # xc90_sim.drivetrain.WheelBearing), not a catastrophic failure mode
    # at this level of model. ASSUMPTION interval/floor for this class.
    "wheel_bearings": WearableComponent(typical_life_miles=120000, floor_condition=0.95),
    # Transmission fluid: ASSUMPTION interval, tracked for maintenance-due
    # purposes (see xc90_sim.transmission.TransmissionFluid) -- doesn't scale
    # any physics itself, the fluid's actual temperature does that.
    "transmission_fluid": WearableComponent(typical_life_miles=60000, floor_condition=1.0),
    # CV joints (front half-shafts only -- rear isn't independently steered
    # in this AWD layout). ASSUMPTION interval; a worn joint's real effect
    # (see xc90_sim.drivetrain.CVJoint) is a small efficiency loss, not
    # gradual torque-curve degradation the way tires/brakes model it.
    "cv_joints": WearableComponent(typical_life_miles=100000, floor_condition=0.95),
    # Engine mounts: this car has a REAL, dated replacement event on record
    # (2024-08-13 @ 92,228mi, see specs/service_history.py) that, until now,
    # this dict didn't include -- meaning that real data point was silently
    # ignored by the wear model despite being genuine CARFAX history.
    # floor_condition=1.0: no direct physics hook exists at this project's
    # level of detail for a worn engine mount (that would need an engine-
    # roll/NVH model this project doesn't have) -- tracked honestly for
    # real maintenance-history fidelity and service_due() purposes only,
    # same reasoning as timing_belt/accessory_belt above, not to scale any
    # physics that doesn't exist yet.
    "engine_mounts": WearableComponent(typical_life_miles=100000, floor_condition=1.0),
}

# ASSUMPTION: typical AGM 12V battery service life is commonly cited around
# 4-6 years of calendar age + charge-cycling, not mileage -- modeled
# separately via age_condition() below. floor_condition=0.6 reflects a
# real, bounded effect (see xc90_sim.electrical.Battery: this scales
# capacity_ah at construction, same "wear evaluated once, not per-tick"
# pattern as tire grip/brake pad condition) -- a badly aged battery has
# less real capacity and sags faster under load, not simply "off".
AGE_WEARABLE_COMPONENTS = {
    "battery_12v": AgeWearableComponent(typical_life_days=1825, floor_condition=0.6),
}


class WearModel:
    def __init__(self, current_mileage=None, history=None):
        self.current_mileage = current_mileage if current_mileage is not None else service_history.CURRENT_MILEAGE
        self.history = history if history is not None else service_history.HISTORY

    def _mileage_at_last_service(self, component):
        replacements = [
            e.mileage for e in self.history
            if e.component == component and e.mileage is not None
        ]
        return max(replacements) if replacements else 0

    def condition(self, component):
        """Returns a 0..1 condition fraction (1.0 = fresh) for a wearable component."""
        spec = WEARABLE_COMPONENTS[component]
        miles_since_service = max(0, self.current_mileage - self._mileage_at_last_service(component))
        wear_frac = min(1.0, miles_since_service / spec.typical_life_miles)
        return 1.0 - wear_frac * (1.0 - spec.floor_condition)

    def miles_since_service(self, component):
        return max(0, self.current_mileage - self._mileage_at_last_service(component))

    def service_due(self, component):
        """True once a component has passed its typical service life —
        meaningful even for components like timing_belt/accessory_belt
        whose floor_condition is 1.0 (no physics degradation modeled),
        where this is the only signal that maintenance is actually due."""
        spec = WEARABLE_COMPONENTS[component]
        return self.miles_since_service(component) >= spec.typical_life_miles

    def _date_at_last_service(self, component):
        matches = [e.date for e in self.history if e.component == component]
        if matches:
            return max(matches)  # ISO "YYYY-MM-DD" strings sort correctly lexicographically
        manufactured = [e.date for e in self.history if e.component == "manufactured"]
        return manufactured[0] if manufactured else service_history.CURRENT_DATE

    def age_days(self, component):
        last_date = date.fromisoformat(self._date_at_last_service(component))
        current_date = date.fromisoformat(service_history.CURRENT_DATE)
        return max(0, (current_date - last_date).days)

    def age_condition(self, component):
        """Age-based counterpart to condition() — for components (like the
        12V battery) that wear out with calendar time/charge-cycling more
        than mileage. See AGE_WEARABLE_COMPONENTS."""
        spec = AGE_WEARABLE_COMPONENTS[component]
        wear_frac = min(1.0, self.age_days(component) / spec.typical_life_days)
        return 1.0 - wear_frac * (1.0 - spec.floor_condition)

    def age_service_due(self, component):
        spec = AGE_WEARABLE_COMPONENTS[component]
        return self.age_days(component) >= spec.typical_life_days

    def report(self):
        report = {
            component: {
                "condition_pct": round(self.condition(component) * 100.0, 1),
                "miles_since_service": self.miles_since_service(component),
            }
            for component in WEARABLE_COMPONENTS
        }
        report.update({
            component: {
                "condition_pct": round(self.age_condition(component) * 100.0, 1),
                "age_days": self.age_days(component),
            }
            for component in AGE_WEARABLE_COMPONENTS
        })
        return report
