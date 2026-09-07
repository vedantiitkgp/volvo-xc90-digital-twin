"""
Camshaft: owns the real intake/exhaust Valve objects for one cylinder and
exposes crank-angle -> open/closed / lift by delegating to them, rather
than bare boolean functions with the timing math inlined. Real DOHC
4-valve-per-cylinder layout (2 intake + 2 exhaust — see
specs.cylinder.INTAKE_VALVES_PER_CYLINDER/EXHAUST_VALVES_PER_CYLINDER),
though the pair within each type isn't individually differentiated (no
swirl/tumble asymmetry modeled between them).

Stays in crank-angle terms throughout (a real camshaft physically turns at
half crank speed — one cam revolution = 720 crank degrees = one full
4-stroke cycle — see engine.timing_belt for where that 2:1 ratio is
actually enforced) since that's the convention the rest of the combustion
model (Cylinder) uses.

Real, well-known 4-stroke behavior captured here: intake and exhaust
valves are both open briefly around TDC between the exhaust and intake
strokes ("valve overlap") -- not the idealized "one valve closes exactly
when the other opens" simplification cruder models use.
"""

from ..specs import cylinder as specs
from .valve import Valve

_INTAKE_OPEN_DEG = 720.0 - specs.INTAKE_OPEN_DEG_BTDC
_INTAKE_CLOSE_DEG = 180.0 + specs.INTAKE_CLOSE_DEG_ABDC
_EXHAUST_OPEN_DEG = 540.0 - specs.EXHAUST_OPEN_DEG_BBDC
_EXHAUST_CLOSE_DEG = specs.EXHAUST_CLOSE_DEG_ATDC  # wraps past the 720/0 boundary


class Camshaft:
    def __init__(self):
        self.intake_valves = [
            Valve(_INTAKE_OPEN_DEG, _INTAKE_CLOSE_DEG, specs.MAX_INTAKE_LIFT_MM)
            for _ in range(specs.INTAKE_VALVES_PER_CYLINDER)
        ]
        self.exhaust_valves = [
            Valve(_EXHAUST_OPEN_DEG, _EXHAUST_CLOSE_DEG, specs.MAX_EXHAUST_LIFT_MM)
            for _ in range(specs.EXHAUST_VALVES_PER_CYLINDER)
        ]

    def intake_open(self, cylinder_angle_deg):
        return self.intake_valves[0].is_open(cylinder_angle_deg)

    def exhaust_open(self, cylinder_angle_deg):
        return self.exhaust_valves[0].is_open(cylinder_angle_deg)

    def valve_overlap(self, cylinder_angle_deg):
        """True during the real, physical intake/exhaust overlap window at TDC."""
        return self.intake_open(cylinder_angle_deg) and self.exhaust_open(cylinder_angle_deg)

    def intake_lift_mm(self, cylinder_angle_deg):
        return self.intake_valves[0].lift_mm(cylinder_angle_deg)

    def exhaust_lift_mm(self, cylinder_angle_deg):
        return self.exhaust_valves[0].lift_mm(cylinder_angle_deg)
