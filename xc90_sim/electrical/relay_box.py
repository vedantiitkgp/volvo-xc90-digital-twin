"""
Relay box: the real named relays this car's electrical system routes
high-current circuits through — fuel pump, starter, cooling fan, horn,
and the main ECU/ignition-switched power feed. Simulation energizes each
relay's coil each tick from the real signal that should control it; the
relay itself just gates that circuit based on its (possibly faulted)
contact state — see Relay.
"""

from .relay import Relay

RELAY_NAMES = ("fuel_pump", "starter", "cooling_fan", "horn", "main_ecu")


class RelayBox:
    def __init__(self):
        self.relays = {name: Relay() for name in RELAY_NAMES}

    def set_energized(self, name, energized):
        self.relays[name].set_energized(energized)

    def set_stuck_open(self, name, stuck):
        self.relays[name].set_stuck_open(stuck)

    def set_stuck_closed(self, name, stuck):
        self.relays[name].set_stuck_closed(stuck)

    def clear_fault(self, name):
        self.relays[name].set_stuck_open(False)
        self.relays[name].set_stuck_closed(False)

    def contacts_closed(self, name):
        return self.relays[name].contacts_closed
