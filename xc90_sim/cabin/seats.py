"""
Seating: occupancy, seatbelt buckle state, seat heating, power position,
fold-flat mechanism — per seat, across the real 2-3-2 (7-seat) layout.
Occupancy + belt state together drive a real safety feature, the seatbelt
reminder (see Seating.unbelted_occupied_seats): a chime/warning for any
seat that's occupied but not buckled.
"""

from ..specs import cabin as specs


class Seat:
    def __init__(self, has_heating=False, can_fold_flat=False):
        self.occupied = False
        self.seatbelt_buckled = False
        # Occupant Classification System: a real child seat detected in
        # this seat (front passenger only, in practice) suppresses that
        # seat's frontal airbag deployment even while occupied — see
        # xc90_sim.cabin.AirbagSystem. Externally settable, same pattern
        # as occupied/seatbelt_buckled.
        self.child_seat_installed = False
        self.has_heating = has_heating
        self.heating_level = 0  # 0 (off) .. specs.SEAT_HEAT_LEVELS
        self.track_position_pct = 50.0  # 0 = full forward, 100 = full back
        self.recline_pct = 50.0  # 0 = full upright, 100 = full recline
        self.head_restraint_up = True  # folds down for cargo/visibility, esp. 2nd/3rd row
        self.can_fold_flat = can_fold_flat  # 2nd/3rd row only — front seats don't fold flat
        self.folded_flat = False

    def set_occupied(self, occupied):
        if occupied and self.folded_flat:
            return  # can't sit in a folded-flat seat
        self.occupied = occupied
        if not occupied:
            self.seatbelt_buckled = False

    def set_folded_flat(self, folded):
        if not self.can_fold_flat:
            return
        self.folded_flat = folded
        if folded:
            # Can't sit in a folded-flat seat — a real one physically isn't
            # a usable seat shape anymore.
            self.occupied = False
            self.seatbelt_buckled = False

    def set_child_seat_installed(self, installed):
        self.child_seat_installed = installed

    def set_seatbelt_buckled(self, buckled):
        self.seatbelt_buckled = buckled

    def set_heating_level(self, level):
        if not self.has_heating:
            return
        self.heating_level = max(0, min(specs.SEAT_HEAT_LEVELS, level))

    def set_track_position_pct(self, pct):
        self.track_position_pct = max(0.0, min(100.0, pct))

    def set_recline_pct(self, pct):
        self.recline_pct = max(0.0, min(100.0, pct))

    def set_head_restraint_up(self, up):
        self.head_restraint_up = up


class Seating:
    def __init__(self):
        self.seats = {
            "driver": Seat(has_heating=specs.FRONT_SEATS_HEATED),
            "front_passenger": Seat(has_heating=specs.FRONT_SEATS_HEATED),
            "row2_left": Seat(has_heating=specs.REAR_SEATS_HEATED, can_fold_flat=True),
            "row2_right": Seat(has_heating=specs.REAR_SEATS_HEATED, can_fold_flat=True),
            "row3_left": Seat(has_heating=specs.REAR_SEATS_HEATED, can_fold_flat=True),
            "row3_right": Seat(has_heating=specs.REAR_SEATS_HEATED, can_fold_flat=True),
        }

    def unbelted_occupied_seats(self):
        """Real seatbelt-reminder condition: occupied but not buckled."""
        return [name for name, seat in self.seats.items() if seat.occupied and not seat.seatbelt_buckled]

    def rear_seats_folded_flat(self):
        return all(self.seats[name].folded_flat for name in ("row2_left", "row2_right", "row3_left", "row3_right"))
