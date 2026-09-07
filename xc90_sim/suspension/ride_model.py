"""
Full-vehicle ride model: a rigid sprung mass with 3 degrees of freedom —
heave (z), pitch (theta), roll (phi) — suspended on 4 independent corner
springs/dampers, driven by the vehicle's longitudinal/lateral acceleration.

This replaces a quasi-static lever-arm load-transfer formula with genuine
Newton-Euler rigid-body dynamics: body attitude has real inertia and damping,
so load transfer ramps in over a realistic time constant (and can overshoot/
oscillate, e.g. nose bob after a hard launch) rather than snapping to a
steady-state value.

Sign conventions:
  z     > 0  : body has settled deeper into the springs (heave down)
  theta > 0  : squat — rear corners compressed, front corners lifted
  phi   > 0  : right side compressed — the load transfer a LEFT turn causes
               (ay > 0 = left turn, SAE convention), matching the tire model's
               and steering model's convention elsewhere in this package.
"""

from ..specs import suspension as specs
from ..specs import chassis as chassis_specs
from .corner import Corner
from . import linkage_geometry

_G = chassis_specs.GRAVITY_MS2

_FRONT_STATIC_LOAD_N = specs.FRONT_SPRUNG_MASS_PER_CORNER_KG * _G
_REAR_STATIC_LOAD_N = specs.REAR_SPRUNG_MASS_PER_CORNER_KG * _G
_FRONT_SPRUNG_TOTAL_KG = 2.0 * specs.FRONT_SPRUNG_MASS_PER_CORNER_KG
_REAR_SPRUNG_TOTAL_KG = 2.0 * specs.REAR_SPRUNG_MASS_PER_CORNER_KG
_SPRUNG_MASS_KG = _FRONT_SPRUNG_TOTAL_KG + _REAR_SPRUNG_TOTAL_KG

# CG-to-axle arms for the SPRUNG mass specifically (not suspension_specs'
# DIST_CG_TO_FRONT/REAR_M, which are whole-vehicle including unsprung mass —
# using those here would leave a small, permanent resting pitch bias, since
# subtracting a flat per-corner unsprung mass shifts the sprung-mass-only
# front/rear split slightly off the whole-vehicle split).
_SPRUNG_FRONT_FRACTION = _FRONT_SPRUNG_TOTAL_KG / _SPRUNG_MASS_KG
_SPRUNG_F_ARM_M = chassis_specs.WHEELBASE_M * (1.0 - _SPRUNG_FRONT_FRACTION)
_SPRUNG_R_ARM_M = chassis_specs.WHEELBASE_M * _SPRUNG_FRONT_FRACTION

# Roll moment arm is CG height ABOVE THE ROLL AXIS, not above the ground —
# using raw CG height (as if the roll axis were at ground level) overstates
# the roll moment. The roll axis height at the CG's fore-aft position is a
# linear interpolation between the front and rear roll centers (from actual
# linkage geometry — see linkage_geometry.py), weighted by the CG's position
# between the axles.
_FRONT_ROLL_CENTER_M = linkage_geometry.FRONT.roll_center_height_m(specs.FRONT_TRACK_M)
_REAR_ROLL_CENTER_M = linkage_geometry.REAR.roll_center_height_m(specs.REAR_TRACK_M)
_ROLL_AXIS_HEIGHT_AT_CG_M = _FRONT_ROLL_CENTER_M + (_REAR_ROLL_CENTER_M - _FRONT_ROLL_CENTER_M) * (
    _SPRUNG_F_ARM_M / (_SPRUNG_F_ARM_M + _SPRUNG_R_ARM_M)
)
_ROLL_MOMENT_ARM_M = specs.CG_HEIGHT_M - _ROLL_AXIS_HEIGHT_AT_CG_M


class RideModel:
    def __init__(self, bushing_condition=1.0):
        """bushing_condition (0..1, default 1.0 = like new): scales damper
        effectiveness for aged rubber bushings (softer, less precisely
        damped) — see xc90_sim.wear. No specific "bushings replaced" service
        event exists in this car's history, so this ages with the whole
        car's mileage rather than resetting at some past service date."""
        front_damper = specs.FRONT_DAMPER_C_NS_PER_M * bushing_condition
        rear_damper = specs.REAR_DAMPER_C_NS_PER_M * bushing_condition
        self.fl = Corner(specs.FRONT_SPRING_RATE_N_PER_M, front_damper, _FRONT_STATIC_LOAD_N)
        self.fr = Corner(specs.FRONT_SPRING_RATE_N_PER_M, front_damper, _FRONT_STATIC_LOAD_N)
        self.rl = Corner(specs.REAR_SPRING_RATE_N_PER_M, rear_damper, _REAR_STATIC_LOAD_N)
        self.rr = Corner(specs.REAR_SPRING_RATE_N_PER_M, rear_damper, _REAR_STATIC_LOAD_N)

        self.z, self.z_dot = 0.0, 0.0
        self.theta, self.theta_dot = 0.0, 0.0
        self.phi, self.phi_dot = 0.0, 0.0

        self.f_arm = _SPRUNG_F_ARM_M
        self.r_arm = _SPRUNG_R_ARM_M
        self.t_half_f = specs.FRONT_TRACK_M / 2.0
        self.t_half_r = specs.REAR_TRACK_M / 2.0

        self.fl_deflection_m = self.fr_deflection_m = 0.0
        self.rl_deflection_m = self.rr_deflection_m = 0.0

    def step(self, dt, total_mass_kg, ax_mps2, ay_mps2):
        """Returns per-corner normal loads (fl_n, fr_n, rl_n, rr_n) for the traction model."""
        fl_x = self.fl.static_x + self.z - self.f_arm * self.theta - self.t_half_f * self.phi
        fr_x = self.fr.static_x + self.z - self.f_arm * self.theta + self.t_half_f * self.phi
        rl_x = self.rl.static_x + self.z + self.r_arm * self.theta - self.t_half_r * self.phi
        rr_x = self.rr.static_x + self.z + self.r_arm * self.theta + self.t_half_r * self.phi

        fl_xdot = self.z_dot - self.f_arm * self.theta_dot - self.t_half_f * self.phi_dot
        fr_xdot = self.z_dot - self.f_arm * self.theta_dot + self.t_half_f * self.phi_dot
        rl_xdot = self.z_dot + self.r_arm * self.theta_dot - self.t_half_r * self.phi_dot
        rr_xdot = self.z_dot + self.r_arm * self.theta_dot + self.t_half_r * self.phi_dot

        f_fl = self.fl.force(fl_x, fl_xdot)
        f_fr = self.fr.force(fr_x, fr_xdot)
        f_rl = self.rl.force(rl_x, rl_xdot)
        f_rr = self.rr.force(rr_x, rr_xdot)

        # Deflection relative to static ride height, for suspension kinematics
        # (camber/toe curves) — see xc90_sim.suspension.kinematics.
        self.fl_deflection_m = fl_x - self.fl.static_x
        self.fr_deflection_m = fr_x - self.fr.static_x
        self.rl_deflection_m = rl_x - self.rl.static_x
        self.rr_deflection_m = rr_x - self.rr.static_x

        z_ddot = _G - (f_fl + f_fr + f_rl + f_rr) / _SPRUNG_MASS_KG
        # Under forward acceleration (ax>0) inertia pitches the body nose-up
        # (squat at the rear) -> theta increases. Anti-squat (accelerating)
        # / anti-dive (braking) geometry reacts part of this moment directly
        # through the links instead of through the springs — real linkage
        # geometry that genuinely reduces visible pitch, not a fudge factor.
        anti_pitch_fraction = (
            linkage_geometry.REAR_ANTI_SQUAT_FRACTION if ax_mps2 > 0 else linkage_geometry.FRONT_ANTI_DIVE_FRACTION
        )
        pitch_moment_ext = total_mass_kg * ax_mps2 * specs.CG_HEIGHT_M * (1.0 - anti_pitch_fraction)
        theta_ddot = (
            self.f_arm * (f_fl + f_fr) - self.r_arm * (f_rl + f_rr) + pitch_moment_ext
        ) / specs.PITCH_INERTIA_KGM2
        # Under a left turn (ay>0) inertia rolls the body right-side-down ->
        # phi increases. The lever arm is CG height ABOVE THE ROLL AXIS (from
        # actual linkage geometry), not above the ground.
        roll_moment_ext = total_mass_kg * ay_mps2 * _ROLL_MOMENT_ARM_M
        # Anti-roll bars: a direct torsional spring resisting roll angle
        # (their stiffness is specified in specs as Nm/rad directly).
        arb_moment = -(specs.FRONT_ARB_ROLL_STIFFNESS_NM_PER_RAD + specs.REAR_ARB_ROLL_STIFFNESS_NM_PER_RAD) * self.phi
        phi_ddot = (
            self.t_half_f * (f_fl - f_fr) + self.t_half_r * (f_rl - f_rr) + roll_moment_ext + arb_moment
        ) / specs.ROLL_INERTIA_KGM2

        self.z_dot += z_ddot * dt
        self.z += self.z_dot * dt
        self.theta_dot += theta_ddot * dt
        self.theta += self.theta_dot * dt
        self.phi_dot += phi_ddot * dt
        self.phi += self.phi_dot * dt

        unsprung_n = specs.UNSPRUNG_MASS_PER_CORNER_KG * _G
        return f_fl + unsprung_n, f_fr + unsprung_n, f_rl + unsprung_n, f_rr + unsprung_n
