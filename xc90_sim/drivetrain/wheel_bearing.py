"""
Wheel bearing: one per wheel. Real wear item; as a bearing wears it
develops a small amount of extra rolling resistance (and, eventually,
noise/play, not modeled here) — a modest, bounded effect, not exaggerated.
Applied once at Simulation construction time via a rolling-resistance
scale factor (same "wear conditions evaluated at construction, not re-
computed every tick" pattern already used for tire grip / brake pad
condition), not re-evaluated dynamically.
"""

# ASSUMPTION: a fully-worn bearing adds a modest, not dramatic, amount of
# rolling resistance for this class of bearing.
MAX_WEAR_RESISTANCE_INCREASE_FRAC = 0.10


class WheelBearing:
    def __init__(self, condition=1.0):
        self.condition = condition

    def rolling_resistance_scale(self):
        return 1.0 + (1.0 - self.condition) * MAX_WEAR_RESISTANCE_INCREASE_FRAC
