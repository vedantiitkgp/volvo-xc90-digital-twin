"""Open differential: equal torque split, independent wheel speeds."""


class OpenDifferential:
    """
    An ideal open differential sends equal torque to both output shafts
    regardless of their relative speed — it's exactly this property that
    lets one wheel spin freely on ice while its partner (with all the grip)
    gets no more drive force than the spinning one. There's no clutch pack
    or torque-biasing here (this isn't a limited-slip or locking diff).
    """

    def split(self, axle_torque_nm):
        """Returns (left_torque_nm, right_torque_nm)."""
        half = axle_torque_nm / 2.0
        return half, half
