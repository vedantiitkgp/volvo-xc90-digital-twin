"""
3-DOF planar rigid-body vehicle dynamics: body-frame longitudinal velocity
(vx), lateral velocity (vy), and yaw rate (r), plus world-frame position and
heading integrated from them.

This is the single place longitudinal and lateral dynamics meet: all 4
wheels' Fx/Fy feed vx/vy, and the yaw moment is the genuine sum of each
wheel's r x F about the CG — not just "front Fy minus rear Fy" — so a
left/right drive-force imbalance (e.g. one wheel spinning under an open
differential) produces a real yaw moment (torque steer), the same way it
would in an actual car.
"""

import math

from ..specs import chassis as specs
from ..specs import suspension as suspension_specs


class VehicleBody:
    def __init__(self, mass_kg=specs.CURB_MASS_KG, yaw_inertia_kgm2=None, rolling_resistance_scale=1.0):
        """rolling_resistance_scale: real wheel-bearing wear adds a small
        amount of rolling resistance (see xc90_sim.drivetrain.WheelBearing)
        -- evaluated once at construction from the car's actual wear
        condition, same pattern as tire grip_scale/brake pad condition,
        not re-computed every tick."""
        self.mass_kg = mass_kg
        # ASSUMPTION: yaw moment of inertia isn't published; approximate as a
        # uniform rod-ish mass distribution over the wheelbase.
        self.yaw_inertia_kgm2 = yaw_inertia_kgm2 or mass_kg * (specs.WHEELBASE_M ** 2) / 12.0
        self.rolling_resistance_scale = rolling_resistance_scale

        self.vx_mps = 0.0  # body-frame longitudinal velocity
        self.vy_mps = 0.0  # body-frame lateral velocity
        self.yaw_rate_rad_s = 0.0
        self.heading_rad = 0.0
        self.world_x_m = 0.0
        self.world_y_m = 0.0
        self.distance_m = 0.0  # path length traveled (odometer, not displacement)

        self.ax_mps2 = 0.0  # body-frame longitudinal accel, for suspension load transfer
        self.ay_mps2 = 0.0  # body-frame lateral accel, for suspension load transfer

    @property
    def speed_mps(self):
        """Signed ground speed (negative = reversing). Body-frame vx dominates
        for the small sideslip angles this vehicle operates at; used for mph
        telemetry and as the reference speed for aero drag / rolling resistance."""
        return self.vx_mps

    def aero_drag_n(self):
        v = self.vx_mps
        return 0.5 * specs.AIR_DENSITY_KGM3 * specs.DRAG_COEFFICIENT * specs.FRONTAL_AREA_M2 * v * abs(v)

    def rolling_resistance_n(self):
        if self.vx_mps == 0.0:
            return 0.0
        weight_n = self.mass_kg * specs.GRAVITY_MS2
        sign = 1.0 if self.vx_mps > 0 else -1.0
        return sign * specs.ROLLING_RESISTANCE_COEFFICIENT * self.rolling_resistance_scale * weight_n

    def step(self, dt, wheel_forces):
        """
        Advance body-frame velocity, yaw, and world pose by dt seconds.

        wheel_forces: dict of {'fl'|'fr'|'rl'|'rr': (Fx_n, Fy_n)}, in the
        vehicle body frame, from each Wheel.step().
        """
        f_arm, r_arm = suspension_specs.DIST_CG_TO_FRONT_M, suspension_specs.DIST_CG_TO_REAR_M
        half_tf, half_tr = suspension_specs.FRONT_TRACK_M / 2.0, suspension_specs.REAR_TRACK_M / 2.0
        # (x, y) position of each wheel relative to the CG; y+ is left (ISO-like).
        positions = {"fl": (f_arm, half_tf), "fr": (f_arm, -half_tf),
                     "rl": (-r_arm, half_tr), "rr": (-r_arm, -half_tr)}

        total_fx = sum(fx for fx, fy in wheel_forces.values()) - self.aero_drag_n() - self.rolling_resistance_n()
        total_fy = sum(fy for fx, fy in wheel_forces.values())
        # Each wheel's moment about the CG is (r x F)_z = x*Fy - y*Fx; summing
        # these (rather than just "front Fy minus rear Fy") is what lets a
        # left/right Fx imbalance create yaw — impossible in an axle-lumped model.
        yaw_moment = sum(
            positions[corner][0] * fy - positions[corner][1] * fx
            for corner, (fx, fy) in wheel_forces.items()
        )

        # "Felt" acceleration (what an accelerometer at the CG reads, and what
        # should drive suspension squat/dive/roll) is just force/mass — F=ma,
        # nothing more. The rotational cross-terms below (m*(vx_dot - vy*r) =
        # Fx, etc.) belong in the STATE-DERIVATIVE used to integrate velocity,
        # not in the felt acceleration — conflating the two was a real bug:
        # it made lateral g read near-zero during a perfectly steady turn,
        # since vy_dot genuinely goes to ~0 at steady state even though the
        # car is very much still pulling lateral g.
        self.ax_mps2 = total_fx / self.mass_kg
        self.ay_mps2 = total_fy / self.mass_kg
        vx_dot = self.ax_mps2 + self.vy_mps * self.yaw_rate_rad_s
        vy_dot = self.ay_mps2 - self.vx_mps * self.yaw_rate_rad_s
        yaw_accel = yaw_moment / self.yaw_inertia_kgm2

        # No forward-only clamp: vx genuinely goes negative in reverse (see
        # GearSelector/'R' handling in sim/simulation.py) — removing this
        # clamp (it used to floor vx at 0) is what makes reverse driving
        # possible at all, not just a cosmetic gear-selector state.
        self.vx_mps = self.vx_mps + vx_dot * dt
        self.vy_mps += vy_dot * dt
        self.yaw_rate_rad_s += yaw_accel * dt
        self.heading_rad += self.yaw_rate_rad_s * dt

        cos_h, sin_h = math.cos(self.heading_rad), math.sin(self.heading_rad)
        self.world_x_m += (self.vx_mps * cos_h - self.vy_mps * sin_h) * dt
        self.world_y_m += (self.vx_mps * sin_h + self.vy_mps * cos_h) * dt
        self.distance_m += math.hypot(self.vx_mps, self.vy_mps) * dt
