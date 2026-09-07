"""
Flywheel: the actual rotating disc that smooths crank speed pulsations
between combustion pulses — a real, named part, not an invisible number
folded into a single "crank inertia" constant. Its own inertia is DERIVED
(solid-disc formula) from an assumed mass/radius, not guessed directly.
"""

from ..specs import engine as specs


class Flywheel:
    def __init__(self, mass_kg=specs.FLYWHEEL_MASS_KG, radius_m=specs.FLYWHEEL_RADIUS_M):
        self.mass_kg = mass_kg
        self.radius_m = radius_m

    @property
    def inertia_kgm2(self):
        """Solid-disc moment of inertia: I = 0.5 * m * r^2."""
        return 0.5 * self.mass_kg * self.radius_m ** 2
