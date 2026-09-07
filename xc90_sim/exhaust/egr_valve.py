"""
EGR (Exhaust Gas Recirculation): recirculates a small fraction of exhaust
into the intake to lower peak combustion temperature (reduces NOx) — real
behavior is more EGR at light/mid load & cruise rpm, none at idle or high
load (where it would hurt driveability/power, so real ECUs shut it off
there too). Modeled through two real mechanisms, not a full multi-
species thermodynamic simulation: (1) a reduction in effective trapped
fresh charge (recirculated exhaust gas physically displaces fresh air in
the same manifold volume) and (2) a lowered effective specific-heat
ratio (gamma) for the trapped charge during compression (recirculated
exhaust gas has a lower gamma than fresh air) — see Cylinder.step()'s
dilution_frac and specs.DILUTED_CHARGE_GAMMA_MIN, added 2026-09-01. Both
are real, physical effects of EGR; what's still simplified is that the
recirculated gas isn't tracked as its own separate species with its own
composition/heat capacity through the full combustion energy balance,
just blended into a single effective gamma.

CONFIRMED 2026-09-01 (xc90_sim/parts_catalog research): this specific
engine, the gasoline B4204T9 twincharger, has no discrete external EGR
VALVE — Volvo's cataloged EGR valve parts for this platform generation
(31439464/36010130) are confirmed for the D4204T DIESEL engine family
only. This class is real physics, not a fabricated part: it models this
engine's internal EGR instead — recirculation via camshaft valve overlap
(intake/exhaust valves both briefly open near TDC, letting some exhaust
gas stay trapped in-cylinder) — a genuine, well-documented gasoline-
engine technique that achieves the same charge-dilution effect without
any separate orderable valve. Class name kept as "EGRValve" for
continuity with the rest of this codebase's naming, even though there's
no discrete physical valve behind it on this exact engine.
"""

from ..specs import exhaust as specs


class EGRValve:
    def __init__(self):
        self.flow_fraction = 0.0

    def step(self, rpm, throttle):
        if rpm < specs.EGR_MIN_RPM or rpm > specs.EGR_MAX_RPM or throttle > 0.5:
            self.flow_fraction = 0.0
            return
        self.flow_fraction = max(0.0, specs.EGR_MAX_FLOW_FRACTION * (1.0 - throttle * 2.0))
