"""
TPMS (Tire Pressure Monitoring System): per-wheel cold-tire pressure vs. the
vehicle's recommended placard pressure, warning per FMVSS 138's real
25%-low threshold — a genuine safety feature, not just a dashboard icon.
"""

from ..specs import tire as specs

_CORNERS = ("fl", "fr", "rl", "rr")


class TPMS:
    def __init__(self):
        self.pressures_psi = {corner: specs.RECOMMENDED_COLD_PRESSURE_PSI for corner in _CORNERS}

    def set_pressure_psi(self, corner, psi):
        self.pressures_psi[corner] = psi

    def low_pressure_warning(self, corner):
        threshold = specs.RECOMMENDED_COLD_PRESSURE_PSI * specs.TPMS_WARNING_THRESHOLD_FRAC
        return self.pressures_psi[corner] < threshold

    def any_warning(self):
        return any(self.low_pressure_warning(corner) for corner in _CORNERS)
