"""A virtual, in-process CAN bus: publish/subscribe by arbitration ID."""

from collections import defaultdict


class CANBus:
    def __init__(self):
        self._subscribers = defaultdict(list)

    def subscribe(self, arbitration_id, callback):
        """callback(frame: CANFrame) is invoked for every frame sent with this ID."""
        self._subscribers[arbitration_id].append(callback)

    def send(self, frame):
        for callback in self._subscribers.get(frame.arbitration_id, ()):
            callback(frame)
