"""
Trip logger: a CAN-bus datalogger, same idea as real OBD-II/CAN tooling
(python-can/cantools style) — it only sees what's broadcast on the bus, then
accumulates time-weighted usage stats (percent of trip time in each gear,
rpm band, etc.) from decoded signal values.

Each CAN message here is time-weighted by its own transmission period
(carried on the frame — see xc90_sim.ecu.base), not the simulation's dt.
"""

from collections import defaultdict

from ..ecu.engine_ecu import ENGINE_DATA
from ..ecu.transmission_ecu import TRANS_DATA
from ..ecu.chassis_ecu import CHASSIS_DYNAMICS, BRAKE_DATA
from ..ecu.awd_ecu import AWD_DATA

_RPM_BANDS = [
    ("idle (<1200)", 0, 1200),
    ("low (1200-2500)", 1200, 2500),
    ("mid (2500-4000)", 2500, 4000),
    ("high (4000-5700)", 4000, 5700),
    ("redline (5700+)", 5700, float("inf")),
]

_THROTTLE_BANDS = [
    ("off (0%)", 0, 1),
    ("light (1-25%)", 1, 25),
    ("moderate (25-60%)", 25, 60),
    ("heavy (60-100%)", 60, 101),
]


def _band_for(value, bands):
    for label, lo, hi in bands:
        if lo <= value < hi:
            return label
    return bands[-1][0]


class TripLogger:
    def __init__(self, bus):
        self.total_time_s = 0.0

        self.gear_time_s = defaultdict(float)
        self.rpm_band_time_s = defaultdict(float)
        self.throttle_band_time_s = defaultdict(float)
        self.converter_locked_time_s = 0.0
        self.manual_mode_time_s = 0.0
        self.brake_active_time_s = 0.0
        self.front_bias_weighted_sum = 0.0
        self.front_bias_time_s = 0.0
        self.max_lateral_g = 0.0
        self.max_longitudinal_g = 0.0

        bus.subscribe(ENGINE_DATA.arbitration_id, self._on_engine)
        bus.subscribe(TRANS_DATA.arbitration_id, self._on_trans)
        bus.subscribe(AWD_DATA.arbitration_id, self._on_awd)
        bus.subscribe(BRAKE_DATA.arbitration_id, self._on_brake)
        bus.subscribe(CHASSIS_DYNAMICS.arbitration_id, self._on_dynamics)

    def _on_engine(self, frame):
        v = frame.message.decode(frame.data)
        dt = frame.period_s
        self.rpm_band_time_s[_band_for(v["rpm"], _RPM_BANDS)] += dt
        self.throttle_band_time_s[_band_for(v["throttle_pct"], _THROTTLE_BANDS)] += dt

    def _on_trans(self, frame):
        v = frame.message.decode(frame.data)
        dt = frame.period_s
        self.gear_time_s[int(v["gear"])] += dt
        self.total_time_s += dt
        if v["converter_locked"]:
            self.converter_locked_time_s += dt
        if v["manual_mode"]:
            self.manual_mode_time_s += dt

    def _on_awd(self, frame):
        v = frame.message.decode(frame.data)
        dt = frame.period_s
        self.front_bias_weighted_sum += v["front_bias_pct"] * dt
        self.front_bias_time_s += dt

    def _on_brake(self, frame):
        v = frame.message.decode(frame.data)
        if v["brake_pedal_pct"] > 1.0:
            self.brake_active_time_s += frame.period_s

    def _on_dynamics(self, frame):
        v = frame.message.decode(frame.data)
        self.max_lateral_g = max(self.max_lateral_g, abs(v["lateral_accel_g"]))
        self.max_longitudinal_g = max(self.max_longitudinal_g, abs(v["longitudinal_accel_g"]))

    def report(self, distance_m, elapsed_s):
        """Returns a plain dict summary — percentages are of TRANSMISSION-ECU
        sample time (self.total_time_s), which tracks the sim tightly enough
        to use as the trip's time base."""
        T = self.total_time_s or 1e-9
        avg_front_bias = self.front_bias_weighted_sum / (self.front_bias_time_s or 1e-9)

        return {
            "distance_km": distance_m / 1000.0,
            "elapsed_s": elapsed_s,
            "avg_speed_kph": (distance_m / elapsed_s) * 3.6 if elapsed_s > 0 else 0.0,
            "gear_pct": {g: 100.0 * t / T for g, t in sorted(self.gear_time_s.items())},
            "rpm_band_pct": {label: 100.0 * self.rpm_band_time_s.get(label, 0.0) / T for label, _, _ in _RPM_BANDS},
            "throttle_band_pct": {
                label: 100.0 * self.throttle_band_time_s.get(label, 0.0) / T for label, _, _ in _THROTTLE_BANDS
            },
            "converter_locked_pct": 100.0 * self.converter_locked_time_s / T,
            "manual_mode_pct": 100.0 * self.manual_mode_time_s / T,
            "brake_active_pct": 100.0 * self.brake_active_time_s / T,
            "avg_awd_front_bias_pct": avg_front_bias,
            "max_lateral_g": self.max_lateral_g,
            "max_longitudinal_g": self.max_longitudinal_g,
        }
