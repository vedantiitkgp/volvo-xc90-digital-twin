"""
Interior storage: glove box and center console open/closed state. Cargo-area
volume (behind 3rd row / max with rows folded) is a static published spec —
see specs/cabin.py — not modeled here since it has no state of its own; the
cargo area's actual open/closed state is the power tailgate, already in
xc90_sim.body.Closures. available_cargo_volume_l() connects the published
figure to Seating's actual fold state instead of being a bare constant.
"""

from ..specs import cabin as specs


class Storage:
    def __init__(self):
        self.glove_box_open = False
        self.center_console_open = False

    def set_glove_box(self, open_):
        self.glove_box_open = open_

    def set_center_console(self, open_):
        self.center_console_open = open_

    def available_cargo_volume_l(self, seating):
        """
        Volvo publishes two figures: 314L behind the 3rd row (rows up) and
        1,858L with 2nd/3rd rows folded flat — nothing in between, since
        partial-fold configurations (e.g. only the 3rd row folded) aren't
        published. This returns the max figure only once every fold-flat
        seat actually is folded, and the conservative "rows up" figure
        otherwise — an honest simplification, not an interpolation.
        """
        if seating.rear_seats_folded_flat():
            return specs.CARGO_VOLUME_MAX_L
        return specs.CARGO_VOLUME_BEHIND_ROW3_L
