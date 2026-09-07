"""
Body control module domain: doors, hood, power tailgate, central locking.

Not engine/drivetrain/chassis physics — a real BCM's job is discrete state plus a
few simple timers (a power liftgate takes real seconds to open/close; a
lock command can't apply with a door open), which is what this models.
"""

from ..specs import body as specs


class Closures:
    def __init__(self):
        self.door_open = {corner: False for corner in specs.DOORS}
        self.locked = True
        self.driver_only_unlocked = False  # real feature: single-stage (driver door) vs. full unlock
        self.hood_open = False
        self.tailgate_open = False
        self.tailgate_moving = False
        self.auto_lock_enabled = True
        self._tailgate_target_open = False
        self._tailgate_progress_s = 0.0

    def set_door(self, corner, open_):
        """Manually open/close one door (e.g. driver/passenger entry/exit)."""
        self.door_open[corner] = open_
        if open_:
            self.locked = False  # can't be locked with a door standing open

    def any_door_open(self):
        return any(self.door_open.values())

    def set_hood(self, open_):
        self.hood_open = open_

    def request_tailgate(self, open_):
        """Power tailgate: starts a timed open/close cycle, not an instant state flip."""
        if open_ == self.tailgate_open and not self.tailgate_moving:
            return
        self._tailgate_target_open = open_
        self.tailgate_moving = True
        self._tailgate_progress_s = 0.0

    def lock(self):
        if not self.any_door_open():
            self.locked = True
            self.driver_only_unlocked = False

    def unlock(self):
        """Full central unlock — all doors. See also unlock_driver_only()."""
        self.locked = False
        self.driver_only_unlocked = False

    def unlock_driver_only(self):
        """Real single-stage remote-unlock behavior: only the driver's door
        opens on first press; a second press (unlock()) opens the rest."""
        self.locked = False
        self.driver_only_unlocked = True

    def ajar_warning(self):
        """Real BCM warning condition: any closure not fully shut."""
        return self.any_door_open() or self.hood_open or self.tailgate_open or self.tailgate_moving

    def tailgate_progress_frac(self):
        """0..1 through the real actuation cycle — 1.0 whenever the tailgate
        is fully at its target position (open or closed) and not mid-cycle."""
        if not self.tailgate_moving:
            return 1.0
        return min(1.0, self._tailgate_progress_s / specs.TAILGATE_ACTUATION_TIME_S)

    def tailgate_target_open(self):
        """Which way the tailgate is headed — the in-progress target while
        moving, or its settled state otherwise."""
        return self._tailgate_target_open if self.tailgate_moving else self.tailgate_open

    def step(self, dt, vehicle_speed_mps):
        if self.tailgate_moving:
            self._tailgate_progress_s += dt
            if self._tailgate_progress_s >= specs.TAILGATE_ACTUATION_TIME_S:
                self.tailgate_open = self._tailgate_target_open
                self.tailgate_moving = False

        if (self.auto_lock_enabled and not self.locked
                and vehicle_speed_mps >= specs.AUTO_LOCK_SPEED_MPS
                and not self.any_door_open()):
            self.locked = True
