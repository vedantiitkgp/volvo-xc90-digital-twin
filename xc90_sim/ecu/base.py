"""
Base ECU: reads live simulation state and periodically broadcasts it onto a
CANBus as byte-packed frames — matching how a real ECU works (it reports
sensor/calculated values on a schedule; it doesn't run the physics itself).

Physics for every subsystem already lives in xc90_sim.engine/transmission/drivetrain/chassis/
suspension/steering. This layer is purely observational.
"""

from ..network import CANFrame


class ScheduledMessage:
    def __init__(self, message, period_s, value_provider):
        self.message = message
        self.period_s = period_s
        self.value_provider = value_provider
        self.elapsed_s = 0.0


class ECU:
    def __init__(self, bus, name):
        self.bus = bus
        self.name = name
        self._scheduled = []

    def register_message(self, message, period_s, value_provider):
        """value_provider() -> dict of {signal_name: physical_value}, called at send time."""
        self._scheduled.append(ScheduledMessage(message, period_s, value_provider))

    def step(self, dt):
        for entry in self._scheduled:
            entry.elapsed_s += dt
            if entry.elapsed_s < entry.period_s:
                continue
            entry.elapsed_s -= entry.period_s
            values = entry.value_provider()
            payload = entry.message.encode(values)
            self.bus.send(CANFrame(entry.message.arbitration_id, payload, entry.message, entry.period_s))
