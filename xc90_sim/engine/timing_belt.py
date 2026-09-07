"""
Timing belt: the real mechanical link enforcing the camshaft's exact 2:1
speed relationship to the crankshaft — a genuine named component, not an
implicit assumption buried in how crank-angle and camshaft-angle happen to
be tracked elsewhere. condition (0..1, from the wear model) represents
belt stretch/wear; a worn belt causes real, if usually tiny, camshaft
timing retard — modeled as a small angle offset that grows as condition
drops, not a floor on performance the way tire/brake wear is (a timing
belt doesn't gradually rob power the way worn brakes do — it's fine until
it isn't, see wear/wear_model.py's floor_condition=1.0 for this component).
"""

from ..specs import accessories as specs

# ASSUMPTION: real belt-stretch-induced timing retard isn't published for
# this component; a small, plausible maximum drift at full wear.
MAX_WEAR_RETARD_DEG = 2.0


class TimingBelt:
    def __init__(self, condition=1.0):
        self.condition = condition  # 0..1, from WearModel.condition("timing_belt")

    @property
    def ratio(self):
        """Camshaft revolutions per crankshaft revolution — exactly 0.5 for any 4-stroke engine."""
        return specs.CRANK_SPROCKET_TEETH / specs.CAM_SPROCKET_TEETH

    def camshaft_angle_deg(self, crank_angle_deg):
        """The real geometric relationship: cam angle = crank angle * ratio,
        plus a small wear-dependent retard (belt stretch) if condition < 1.0."""
        retard_deg = (1.0 - self.condition) * MAX_WEAR_RETARD_DEG
        return (crank_angle_deg * self.ratio) - retard_deg
