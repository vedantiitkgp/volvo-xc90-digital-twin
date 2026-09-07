"""
Propshaft (driveshaft): connects the front transfer case/Haldex unit to
the rear differential in this AWD car — its own rotational inertia and
torsional stiffness, real named parts of the AWD driveline.

windup_angle_rad is a genuine first-order torsional-lag state: the shaft
doesn't transmit torque instantly, it twists under load (target_windup =
torque/stiffness) and that twist itself lags the commanded torque by
RESPONSE_TAU_S (a real steel shaft's fast-but-nonzero mechanical
response). delivered_torque_nm() reads that lagged state back out as an
actual torque -- CLOSED into the torque path (see Simulation.step(),
which now feeds the rear differential this lagged value instead of the
instantaneous commanded torque). At steady state delivered_torque_nm()
exactly equals the commanded torque (windup settles to torque/stiffness);
only *transients* -- a hard launch, a gearshift -- see the shaft's real
compliance smooth/delay delivery, which is the actual physical effect
being modeled, not a re-derivation of the full multi-body AWD driveline
(propshaft inertia interacting with the Haldex clutch and differential
dynamics in full generality remains out of scope -- this is a first-order
approximation of that system's dominant torsional mode, not the whole
thing).
"""

# ASSUMPTION: neither is independently published for this exact part.
# TORSIONAL_STIFFNESS_NM_PER_RAD revised 2026-09-01 (was 8000, which
# produced an unrealistic ~40 degrees of windup at this car's peak
# simulated rear-axle torque during a hard launch -- real steel propshaft
# windup at peak torque is a few degrees at most). Re-estimated from
# G*J/L for a plausible tubular propshaft (steel, G=79 GPa, ~70mm OD/64mm
# ID, ~1.5m length): J=pi/32*(OD^4-ID^4)=7.1e-7 m^4, k=G*J/L=~37,000
# Nm/rad -- rounded to a plausible 40,000 Nm/rad, giving ~8-9 degrees of
# windup at this car's peak simulated axle torque, in a defensible range
# for this class of shaft rather than a bare guess.
INERTIA_KGM2 = 0.02
TORSIONAL_STIFFNESS_NM_PER_RAD = 40000.0
RESPONSE_TAU_S = 0.02  # fast mechanical response


class Propshaft:
    def __init__(self):
        self.windup_angle_rad = 0.0

    def step(self, dt, rear_torque_nm):
        target_windup_rad = rear_torque_nm / TORSIONAL_STIFFNESS_NM_PER_RAD
        alpha = dt / (RESPONSE_TAU_S + dt)
        self.windup_angle_rad += alpha * (target_windup_rad - self.windup_angle_rad)

    def delivered_torque_nm(self):
        return TORSIONAL_STIFFNESS_NM_PER_RAD * self.windup_angle_rad
