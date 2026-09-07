"""
Turbocharger: the exhaust-driven half of this twincharger system, reified
as its own component (previously this exact lag logic lived as bare
methods directly on Engine — same physics, now with a real named part
owning its own state). Boost genuinely lags toward its rpm/throttle-
dependent target — the real physical reason turbo lag exists at all (the
turbine has to spin up using exhaust energy, unlike the supercharger,
which is belt-driven and therefore instant — see AccessoryBelt/
specs.cylinder's supercharger constants).
"""

import numpy as np

from ..specs import cylinder as cyl_specs
from ..specs import engine as engine_specs


class Turbocharger:
    def __init__(self):
        self.boost_pa = 0.0

    def step(self, dt, rpm, throttle):
        spool_frac = np.clip(
            (rpm - cyl_specs.TURBO_SPOOL_START_RPM) / (cyl_specs.TURBO_FULL_BOOST_RPM - cyl_specs.TURBO_SPOOL_START_RPM),
            0.0, 1.0,
        )
        target_boost_pa = cyl_specs.TURBO_MAX_BOOST_PA * spool_frac * throttle
        alpha = dt / (engine_specs.BOOST_LAG_TAU_S + dt)
        self.boost_pa += alpha * (target_boost_pa - self.boost_pa)

    def reset(self):
        """Ignition off / engine off: the turbine spins down, no residual boost."""
        self.boost_pa = 0.0
