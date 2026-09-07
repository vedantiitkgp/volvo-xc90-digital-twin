"""Single-corner spring + damper force model (stateless: compression state lives in the rigid body)."""

from ..specs import suspension as specs


class Corner:
    """
    A quarter-car spring/damper: given how far it's compressed and how fast
    that's changing, returns the force it pushes back on the body with (which,
    by Newton's third law, is also the load it presses into the tire with).

    Bump/droop stops are a simplified stiffness multiplier beyond the travel
    limit, not a smooth progressive curve.
    """

    def __init__(self, spring_rate_n_per_m, damper_c_ns_per_m, static_load_n):
        self.k = spring_rate_n_per_m
        self.c = damper_c_ns_per_m
        self.static_x = static_load_n / spring_rate_n_per_m  # static sag reference, m

    def _effective_stiffness(self, x):
        if x > self.static_x + specs.BUMP_TRAVEL_M or x < self.static_x - specs.DROOP_TRAVEL_M:
            return self.k * specs.BUMP_STOP_STIFFNESS_MULTIPLIER
        return self.k

    def force(self, compression_m, compression_rate_mps):
        k_eff = self._effective_stiffness(compression_m)
        return max(0.0, k_eff * compression_m + self.c * compression_rate_mps)
