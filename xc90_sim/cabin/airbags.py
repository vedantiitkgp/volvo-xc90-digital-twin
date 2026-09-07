"""
Airbags/SRS: crash sensing off the real body-frame accelerometer data
(VehicleBody.ax_mps2/ay_mps2 — the same signal the chassis ECU already
reports as accel_g/lateral_accel_g), driver+passenger frontal bags, front
side (thorax) bags, full-length curtain bags, and seatbelt pretensioners.

Composed here rather than inside VehicleBody/Seating themselves — same
"compose at the Simulation level" pattern used for dome_light_on/
brake_lights_on elsewhere in this project — so AirbagSystem stays testable
standalone by just calling step(dt, ax_mps2, ay_mps2, power_on) with any
values.

Deployment is one-time and permanent for the rest of the sim run (real
airbags are single-use pyrotechnic devices requiring physical replacement
and aren't re-armed by driving on) — there is no reset short of building a
new AirbagSystem/Simulation.
"""

from ..specs import airbags as specs


class Airbag:
    def __init__(self, location):
        self.location = location
        self.deployed = False

    def deploy(self):
        self.deployed = True


class AirbagSystem:
    def __init__(self, seating):
        self.seating = seating
        self.airbags = {
            "driver_frontal": Airbag("driver_frontal"),
            "passenger_frontal": Airbag("passenger_frontal"),
            "driver_side": Airbag("driver_side"),
            "passenger_side": Airbag("passenger_side"),
            "curtain_left": Airbag("curtain_left"),
            "curtain_right": Airbag("curtain_right"),
        }
        self.pretensioners_fired = set()  # seat names
        # SRS self-test: real dash light does a bulb-check flash for a few
        # seconds at power-on, then goes off if nothing's wrong. self_test_fault
        # is an externally-settable fault-injection hook (e.g. a buckle-switch
        # continuity fault, a clockspring fault) — same virtual-fault pattern
        # as Relay/Fuse elsewhere, since this project doesn't simulate the
        # wiring-level physics of those specific faults.
        self.self_test_fault = False
        self._power_on_elapsed_s = 0.0
        self._was_power_on = False

    def set_self_test_fault(self, fault):
        self.self_test_fault = fault

    def step(self, dt, ax_mps2, ay_mps2, power_on):
        if power_on and not self._was_power_on:
            self._power_on_elapsed_s = 0.0
        if power_on:
            self._power_on_elapsed_s += dt
        self._was_power_on = power_on
        self._step_crash_sensing(ax_mps2, ay_mps2)

    def _step_crash_sensing(self, ax_mps2, ay_mps2):
        ax_g = ax_mps2 / specs.GRAVITY_MS2
        ay_g = ay_mps2 / specs.GRAVITY_MS2
        crash_event = False

        if ax_g <= -specs.FRONTAL_DEPLOY_THRESHOLD_G:
            self.airbags["driver_frontal"].deploy()
            crash_event = True
            # Real Occupant Classification System: an empty seat OR a
            # detected child seat suppresses the passenger frontal bag —
            # see Seat.child_seat_installed.
            front_passenger = self.seating.seats["front_passenger"]
            if front_passenger.occupied and not front_passenger.child_seat_installed:
                self.airbags["passenger_frontal"].deploy()

        # A real car has independent sensors per side; not modeled at that
        # granularity here — a strong lateral pulse deploys the near-side
        # thorax bag and the full-length curtain on that side.
        if ay_g >= specs.SIDE_DEPLOY_THRESHOLD_G:
            self.airbags["driver_side"].deploy()
            self.airbags["curtain_left"].deploy()
            crash_event = True
        elif ay_g <= -specs.SIDE_DEPLOY_THRESHOLD_G:
            self.airbags["passenger_side"].deploy()
            self.airbags["curtain_right"].deploy()
            crash_event = True

        if crash_event:
            # Pretensioners fire with any deployment, but only do anything
            # real for an occupant who's actually buckled in — same logic
            # a real system applies via its buckle switches.
            for name, seat in self.seating.seats.items():
                if seat.occupied and seat.seatbelt_buckled:
                    self.pretensioners_fired.add(name)

    def any_deployed(self):
        return any(bag.deployed for bag in self.airbags.values())

    def warning_light_on(self):
        """Real SRS light: on during the power-on bulb check, on
        permanently if any airbag has deployed, or on if a self-test fault
        is present (buckle-switch continuity, clockspring, etc. — the real
        FAULT physics isn't simulated, but self_test_fault gives this a
        genuine, connected hook to set one — see set_self_test_fault())."""
        bulb_check_active = self._was_power_on and self._power_on_elapsed_s < specs.SRS_BULB_CHECK_DURATION_S
        return self.any_deployed() or self.self_test_fault or bulb_check_active
