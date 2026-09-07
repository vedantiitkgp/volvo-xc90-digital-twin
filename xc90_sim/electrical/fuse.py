"""
Fuse box: real named circuits, each protected by a fuse with a real
amperage rating (see specs/accessories.py). Under normal operation these
never blow — fuses are sized with headroom over normal load, same as a
real car — but a forced short (force_short(), a test/diagnostic hook,
since this project has no per-wire short-circuit physics) draws far more
current than the rating and blows it, cutting that circuit until
replaced. Same pattern as this project's other externally-driven faults
(e.g. Airbags/AdaptiveCruise's virtual sensors): the physics of the FAULT
itself isn't simulated, but the CONSEQUENCE of one is real and connected.
"""

from ..specs import accessories as specs

FUSE_RATINGS_A = {
    "headlights": specs.FUSE_RATING_HEADLIGHTS_A,
    "wipers": specs.FUSE_RATING_WIPERS_A,
    "horn": specs.FUSE_RATING_HORN_A,
    "fuel_pump": specs.FUSE_RATING_FUEL_PUMP_A,
    "cooling_fan": specs.FUSE_RATING_COOLING_FAN_A,
    "dome_light": specs.FUSE_RATING_DOME_LIGHT_A,
    "infotainment": specs.FUSE_RATING_INFOTAINMENT_A,
    "ecu_main": specs.FUSE_RATING_ECU_MAIN_A,
}


class Fuse:
    def __init__(self, rated_amps):
        self.rated_amps = rated_amps
        self.blown = False
        self.pulled = False  # manually removed by hand -- distinct real state from blown-by-overcurrent
        self._forced_short = False

    def force_short(self, shorted=True):
        self._forced_short = shorted

    def check(self, amps):
        if self.blown:
            return
        if self._forced_short or amps > self.rated_amps:
            self.blown = True

    def pull(self):
        self.pulled = True

    def replace(self):
        self.blown = False
        self.pulled = False
        self._forced_short = False

    def is_out(self):
        """The circuit is dead either way — blown (fault) or pulled (manual)."""
        return self.blown or self.pulled


class FuseBox:
    def __init__(self):
        self.fuses = {name: Fuse(rated_amps) for name, rated_amps in FUSE_RATINGS_A.items()}

    def check(self, name, amps):
        self.fuses[name].check(amps)

    def is_blown(self, name):
        return self.fuses[name].is_out()

    def pull(self, name):
        self.fuses[name].pull()

    def force_short(self, name, shorted=True):
        self.fuses[name].force_short(shorted)

    def replace(self, name):
        self.fuses[name].replace()
