"""Cabin electronics ECU: HVAC, park-assist, infotainment, seatbelt-reminder, BLIS, TPMS, oil life."""

from ..network import CANMessage, CANSignal
from .base import ECU

HVAC_DATA = CANMessage(
    arbitration_id=0x1B0,
    name="HVAC_DATA",
    signals=[
        CANSignal("cabin_temp_c", num_bytes=2, scale=0.1, signed=True, unit="C"),
        CANSignal("target_temp_c", num_bytes=2, scale=0.1, signed=True, unit="C"),
        CANSignal("fan_speed", num_bytes=1, scale=1.0),
        CANSignal("power_on", num_bytes=1, scale=1.0),
    ],
)

PARK_ASSIST_DATA = CANMessage(
    arbitration_id=0x1B1,
    name="PARK_ASSIST_DATA",
    signals=[
        CANSignal("front_distance_cm", num_bytes=1, scale=1.0, unit="cm"),  # 255 = none detected
        CANSignal("rear_distance_cm", num_bytes=1, scale=1.0, unit="cm"),
    ],
)

INFOTAINMENT_DATA = CANMessage(
    arbitration_id=0x1B2,
    name="INFOTAINMENT_DATA",
    signals=[
        CANSignal("power_on", num_bytes=1, scale=1.0),
        CANSignal("volume_pct", num_bytes=1, scale=1.0, unit="%"),
        CANSignal("muted", num_bytes=1, scale=1.0),
    ],
)

SEATBELT_DATA = CANMessage(
    arbitration_id=0x1B3,
    name="SEATBELT_DATA",
    signals=[
        CANSignal("driver_belted", num_bytes=1, scale=1.0),
        CANSignal("front_passenger_belted", num_bytes=1, scale=1.0),
        CANSignal("any_unbelted_occupied", num_bytes=1, scale=1.0),
    ],
)

BLIS_DATA = CANMessage(
    arbitration_id=0x1B4,
    name="BLIS_DATA",
    signals=[
        CANSignal("left_warning", num_bytes=1, scale=1.0),
        CANSignal("right_warning", num_bytes=1, scale=1.0),
    ],
)

TPMS_DATA = CANMessage(
    arbitration_id=0x1B5,
    name="TPMS_DATA",
    signals=[
        CANSignal("fl_psi", num_bytes=1, scale=0.5, unit="psi"),
        CANSignal("fr_psi", num_bytes=1, scale=0.5, unit="psi"),
        CANSignal("rl_psi", num_bytes=1, scale=0.5, unit="psi"),
        CANSignal("rr_psi", num_bytes=1, scale=0.5, unit="psi"),
        CANSignal("warning", num_bytes=1, scale=1.0),
    ],
)

MAINTENANCE_DATA = CANMessage(
    arbitration_id=0x1B6,
    name="MAINTENANCE_DATA",
    signals=[
        CANSignal("oil_life_pct", num_bytes=1, scale=1.0, unit="%"),
        CANSignal("oil_change_due", num_bytes=1, scale=1.0),
        CANSignal("fuel_level_pct", num_bytes=1, scale=1.0, unit="%"),
        CANSignal("low_fuel_warning", num_bytes=1, scale=1.0),
    ],
)

_NO_OBSTACLE_CM = 255


def _distance_cm(distance_m):
    if distance_m is None:
        return _NO_OBSTACLE_CM
    return min(_NO_OBSTACLE_CM - 1, round(distance_m * 100.0))


class CabinECU(ECU):
    def __init__(self, bus, hvac, parking_assist, infotainment, seating, blind_spot_monitor, body,
                 tpms, oil_life_monitor, fuel_tank):
        super().__init__(bus, "CabinECU")
        self.hvac = hvac
        self.parking_assist = parking_assist
        self.infotainment = infotainment
        self.seating = seating
        self.blind_spot_monitor = blind_spot_monitor
        self.body = body
        self.tpms = tpms
        self.oil_life_monitor = oil_life_monitor
        self.fuel_tank = fuel_tank
        self.register_message(HVAC_DATA, period_s=0.5, value_provider=self._hvac_values)  # 2 Hz
        self.register_message(PARK_ASSIST_DATA, period_s=0.1, value_provider=self._park_values)  # 10 Hz
        self.register_message(INFOTAINMENT_DATA, period_s=0.5, value_provider=self._infotainment_values)
        self.register_message(SEATBELT_DATA, period_s=0.2, value_provider=self._seatbelt_values)  # 5 Hz
        self.register_message(BLIS_DATA, period_s=0.1, value_provider=self._blis_values)  # 10 Hz
        self.register_message(TPMS_DATA, period_s=1.0, value_provider=self._tpms_values)  # 1 Hz -- slow-changing
        self.register_message(MAINTENANCE_DATA, period_s=2.0, value_provider=self._maintenance_values)

    def _hvac_values(self):
        return {
            "cabin_temp_c": self.hvac.cabin_temp_c,
            "target_temp_c": self.hvac.target_temp_c,
            "fan_speed": self.hvac.fan_speed,
            "power_on": 1 if self.hvac.power_on else 0,
        }

    def _park_values(self):
        return {
            "front_distance_cm": _distance_cm(self.parking_assist.front_distance_m),
            "rear_distance_cm": _distance_cm(self.parking_assist.rear_distance_m),
        }

    def _infotainment_values(self):
        return {
            "power_on": 1 if self.infotainment.power_on else 0,
            "volume_pct": self.infotainment.volume_pct,
            "muted": 1 if self.infotainment.muted else 0,
        }

    def _seatbelt_values(self):
        unbelted = self.seating.unbelted_occupied_seats()
        rear_seats = ("row2_left", "row2_right", "row3_left", "row3_right")
        return {
            "driver_belted": 0 if "driver" in unbelted else 1,
            "front_passenger_belted": 0 if "front_passenger" in unbelted else 1,
            "any_unbelted_occupied": 1 if any(s in unbelted for s in rear_seats) else 0,
        }

    def _blis_values(self):
        speed_mps = self.body.speed_mps
        return {
            "left_warning": 1 if self.blind_spot_monitor.left_warning(speed_mps) else 0,
            "right_warning": 1 if self.blind_spot_monitor.right_warning(speed_mps) else 0,
        }

    def _tpms_values(self):
        p = self.tpms.pressures_psi
        return {
            "fl_psi": p["fl"], "fr_psi": p["fr"], "rl_psi": p["rl"], "rr_psi": p["rr"],
            "warning": 1 if self.tpms.any_warning() else 0,
        }

    def _maintenance_values(self):
        return {
            "oil_life_pct": round(self.oil_life_monitor.life_pct()),
            "oil_change_due": 1 if self.oil_life_monitor.change_due() else 0,
            "fuel_level_pct": round(self.fuel_tank.level_fraction() * 100.0),
            "low_fuel_warning": 1 if self.fuel_tank.low_fuel_warning() else 0,
        }
