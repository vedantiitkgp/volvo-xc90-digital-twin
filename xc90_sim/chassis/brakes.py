"""Friction brake system: pedal input -> front/rear axle brake torque."""

from ..specs import chassis as specs


class Brakes:
    """
    Converts a 0..1 brake pedal input into front/rear axle torques. These are
    fed into the same traction-limited Axle model as drive torque, so hard
    braking beyond available grip shows up as wheel slip there rather than
    being handled as a separate idealized deceleration.
    """

    def __init__(self, mass_kg=specs.CURB_MASS_KG, front_pad_condition=1.0, rear_pad_condition=1.0):
        """
        front_pad_condition / rear_pad_condition (0..1, default 1.0 = fresh):
        scales that axle's max brake force for pad/rotor wear — see xc90_sim.wear.
        """
        self.mass_kg = mass_kg
        self.pedal = 0.0  # 0..1
        self.front_pad_condition = front_pad_condition
        self.rear_pad_condition = rear_pad_condition

    def set_pedal(self, pedal):
        self.pedal = max(0.0, min(1.0, pedal))

    def axle_torques_nm(self, vehicle_speed_mps, dt, booster_assist_frac=1.0):
        """Returns (front_axle_torque_nm, rear_axle_torque_nm), opposing motion.

        booster_assist_frac (0..1, default 1.0 = full assist): real vacuum-
        assist degradation from a depleted brake-booster reservoir — see
        xc90_sim.chassis.BrakeBooster/VacuumPump. Same pedal input produces
        less deceleration when assist is degraded, the real "pedal goes
        hard" symptom of insufficient booster vacuum.
        """
        if abs(vehicle_speed_mps) < 1e-3:
            return 0.0, 0.0

        max_decel_mps2 = specs.MAX_BRAKE_DECEL_G * specs.GRAVITY_MS2 * self.pedal * booster_assist_frac
        # Cap deceleration at whatever brings the car to exactly a dead stop
        # this tick — a real friction brake can't push a vehicle backward
        # past a stop (once relative sliding velocity hits zero, static
        # friction just holds it). Without this, discrete-timestep braking
        # right near v=0 overshoots past zero and the sign flip below then
        # "brakes" it back the other way — forever, chattering across zero
        # instead of settling. This was silently masked before by an
        # unrelated forward-only clamp on vx that no longer exists now that
        # reverse driving is real (see GearSelector/'R').
        max_stopping_decel_mps2 = abs(vehicle_speed_mps) / dt
        effective_decel_mps2 = min(max_decel_mps2, max_stopping_decel_mps2)

        total_force_n = self.mass_kg * effective_decel_mps2
        sign = 1.0 if vehicle_speed_mps > 0 else -1.0
        front_force_n = total_force_n * specs.BRAKE_FRONT_BIAS * self.front_pad_condition
        rear_force_n = total_force_n * (1.0 - specs.BRAKE_FRONT_BIAS) * self.rear_pad_condition

        radius = specs.TIRE_ROLLING_RADIUS_M
        return -sign * front_force_n * radius, -sign * rear_force_n * radius
