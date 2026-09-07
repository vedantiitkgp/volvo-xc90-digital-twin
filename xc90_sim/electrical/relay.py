"""
Automotive relay: a low-current coil-energized switch that gates a
high-current circuit. Real cars route meaningful loads (fuel pump,
starter, cooling fan, horn) through relays like this rather than the
switch/ECU pin directly, since neither is rated for that much current.

Modeled with a genuine fault-injection hook (stuck open / stuck closed) —
a relay failing is a real, well-known automotive fault (a stuck-open fuel
pump relay means the engine cranks but never catches; a stuck-closed
cooling fan relay means the fan runs continuously even with the key off,
draining the battery) — not just a decorative pass-through with no way to
ever see it do anything.
"""


class Relay:
    def __init__(self):
        self.energized = False
        self.stuck_open = False
        self.stuck_closed = False

    def set_energized(self, energized):
        self.energized = energized

    def set_stuck_open(self, stuck):
        self.stuck_open = stuck

    def set_stuck_closed(self, stuck):
        self.stuck_closed = stuck

    @property
    def contacts_closed(self):
        if self.stuck_open:
            return False
        if self.stuck_closed:
            return True
        return self.energized
