"""Nonlinear, saturating tire force model (simplified Magic Formula + friction ellipse)."""

import math

from ..specs import tire as specs
from ..specs import chassis as chassis_specs


def _magic_formula(slip, B, C, E, peak_force_n):
    """Pacejka-style pure-slip curve: force rises ~linearly at small slip,
    peaks, then (mildly) falls off — this is what "saturating" buys you over
    a Coulomb cap: the tire actually has a grip peak, not a flat ceiling."""
    Bx = B * slip
    return peak_force_n * math.sin(C * math.atan(Bx - E * (Bx - math.atan(Bx))))


class TireModel:
    """
    Computes combined longitudinal (Fx) and lateral (Fy) tire force from
    slip ratio, slip angle, and normal load, using independent pure-slip
    Magic Formula curves combined through a friction ellipse — the standard
    lightweight way to approximate that a tire has one shared grip budget
    for braking/driving and cornering, not two independent ones.

    grip_scale (0..1, default 1.0 = brand new): scales peak grip down for
    tire wear — see xc90_sim.wear. A worn tire's grip *peak* drops; this
    model doesn't also shift *where* (what slip ratio/angle) that peak
    occurs, which real tread wear does slightly.
    """

    def __init__(self, grip_scale=1.0):
        self.grip_scale = grip_scale

    def forces(self, slip_ratio, slip_angle_rad, normal_load_n):
        peak_force_n = self.grip_scale * chassis_specs.TIRE_FRICTION_COEFFICIENT * max(0.0, normal_load_n)
        if peak_force_n < 1e-6:
            return 0.0, 0.0

        fx_pure = _magic_formula(slip_ratio, specs.LONG_B, specs.LONG_C, specs.LONG_E, peak_force_n)
        fy_pure = _magic_formula(slip_angle_rad, specs.LAT_B, specs.LAT_C, specs.LAT_E, peak_force_n)

        magnitude = math.hypot(fx_pure, fy_pure)
        if magnitude <= peak_force_n or magnitude < 1e-9:
            return fx_pure, fy_pure

        scale = peak_force_n / magnitude  # friction-ellipse clamp
        return fx_pure * scale, fy_pure * scale
