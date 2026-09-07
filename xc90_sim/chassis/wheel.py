"""Single-wheel tire model: rotational dynamics driven by a nonlinear, saturating tire."""

from ..specs import chassis as specs
from ..specs import tire as tire_specs
from .tire_model import TireModel


class Wheel:
    """
    One wheel's rotational dynamics + tire forces. Longitudinal slip ratio
    and lateral slip angle are computed from this wheel's own speed and the
    vehicle's velocity at its corner, then handed to a TireModel for
    combined-slip Fx/Fy — a genuine slip-based tire model, not a Coulomb
    "mu*N never exceeded" cap, so it captures peak grip and (mild) falloff
    beyond it.

    Four of these (FL/FR/RL/RR) plus an open differential on each axle (see
    xc90_sim.drivetrain.differential) reproduce real per-wheel behavior:
    one wheel can spin while its partner doesn't, left/right load differs
    under roll, and a left/right drive-force imbalance creates a genuine
    yaw moment (torque steer) — none of which a single lumped axle can do.
    """

    def __init__(self, grip_scale=1.0):
        self.omega = 0.0  # rad/s
        self.tire = TireModel(grip_scale=grip_scale)
        self.slip_ratio = 0.0
        self.slip_angle_rad = 0.0

    def step(self, dt, drive_torque_nm, brake_torque_nm, vx_mps, vy_at_wheel_mps, steer_angle_rad,
              normal_load_n, camber_rad=0.0):
        """
        Returns (Fx_n, Fy_n): longitudinal and lateral tire force delivered
        to the vehicle body, in the vehicle body frame.

        drive_torque_nm / brake_torque_nm: kept separate (not pre-summed)
        because they're physically different: drive torque is a MOTIVE
        torque that can freely spin the wheel through zero into the
        opposite rotational direction (e.g. accelerating from a stop in
        reverse); brake torque is a DISSIPATIVE friction torque that can
        only ever decelerate the wheel toward zero relative rotation and
        stop there — it has no mechanism to add energy that spins the
        wheel the other way. See the clamp below for why that distinction
        matters once brake torque exceeds available tire grip.
        vx_mps: body-frame longitudinal speed AT THIS WHEEL (differs left vs.
        right under yaw rate — the outer wheel in a turn travels faster).
        vy_at_wheel_mps: body-frame lateral speed at this wheel's location
        (differs front vs. rear under yaw rate).
        steer_angle_rad: driver steer angle plus any kinematic toe (0 for a
        rear wheel with no toe contribution).
        camber_rad: current camber angle (from suspension kinematics), used
        for camber thrust — a cambered tire generates lateral force even at
        zero slip angle.
        """
        radius = specs.TIRE_ROLLING_RADIUS_M
        wheel_surface_speed = self.omega * radius
        denom = max(abs(vx_mps), abs(wheel_surface_speed), tire_specs.SLIP_SPEED_EPSILON_MPS)
        kappa_target = (wheel_surface_speed - vx_mps) / denom

        vx_safe = max(abs(vx_mps), tire_specs.SLIP_SPEED_EPSILON_MPS)
        alpha_target = steer_angle_rad - vy_at_wheel_mps / vx_safe

        # Relax toward the kinematic targets over the tire's relaxation
        # length rather than snapping to them instantly (see specs.tire).
        rolling_speed = max(abs(vx_mps), tire_specs.SLIP_SPEED_EPSILON_MPS)
        kappa_rate = rolling_speed / tire_specs.LONGITUDINAL_RELAXATION_LENGTH_M
        alpha_rate = rolling_speed / tire_specs.LATERAL_RELAXATION_LENGTH_M
        self.slip_ratio += (kappa_target - self.slip_ratio) * min(1.0, kappa_rate * dt)
        self.slip_angle_rad += (alpha_target - self.slip_angle_rad) * min(1.0, alpha_rate * dt)

        fx, fy = self.tire.forces(self.slip_ratio, self.slip_angle_rad, normal_load_n)
        # Camber thrust is additive on top of the slip-generated (combined-
        # ellipse-limited) force, not folded into the ellipse itself — a
        # simplification, but camber angles here are small (a few degrees at
        # most) so the thrust is a minor correction, not a dominant term.
        fy += tire_specs.CAMBER_THRUST_COEFFICIENT * camber_rad * normal_load_n

        reaction_torque = fx * radius
        domega_dt = (drive_torque_nm + brake_torque_nm - reaction_torque) / specs.WHEEL_INERTIA_KGM2
        new_omega = self.omega + domega_dt * dt

        # Once commanded brake torque exceeds what the tire's (now-saturated)
        # reaction can resist, the excess would otherwise spin the wheel up
        # in the opposite direction indefinitely — a real friction brake has
        # no way to do that (it only ever removes rotational energy). If
        # braking was active and the sign of omega would flip this tick,
        # that's the wheel reaching zero relative rotation (lockup/stop),
        # not an overshoot into reverse spin — clamp to exactly 0 instead.
        # (No forward-only clamp otherwise: omega genuinely goes negative
        # under reverse gear's negative drive torque — see GearSelector/'R'
        # in sim/simulation.py — a real wheel can spin either direction.)
        if brake_torque_nm != 0.0 and (new_omega * self.omega < 0.0 or self.omega == 0.0):
            # The `self.omega == 0.0` half matters just as much as the sign-
            # flip check: once a locked wheel is clamped to exactly 0, the
            # very next tick's sign-flip test (new*old) is always 0 (never
            # negative) since old=0 — without this, the wheel would run
            # away again from a standing start every tick after the first,
            # rather than staying locked for as long as braking dominates.
            new_omega = 0.0
        self.omega = new_omega

        return fx, fy
