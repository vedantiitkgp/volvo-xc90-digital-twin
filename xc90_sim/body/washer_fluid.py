"""Windshield washer fluid reservoir: a real, small consumable — depleted by actual spray events."""

from ..specs import body as specs


class WasherFluid:
    def __init__(self, level_l=None):
        self.level_l = specs.WASHER_FLUID_CAPACITY_L if level_l is None else level_l

    def spray(self):
        self.level_l = max(0.0, self.level_l - specs.WASHER_FLUID_SPRAY_VOLUME_L)

    def refill(self, liters=None):
        target = specs.WASHER_FLUID_CAPACITY_L if liters is None else self.level_l + liters
        self.level_l = min(specs.WASHER_FLUID_CAPACITY_L, target)

    def low_warning(self):
        return self.level_l <= specs.WASHER_FLUID_LOW_WARNING_L
