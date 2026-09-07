"""
Oxygen (O2 / lambda) sensor: reads the REAL air-fuel ratio the cylinders
are actually running (from the combustion model's own fuel injection, not
an assumed value), converted to lambda (1.0 = stoichiometric), with a
real response lag and measurement noise — same "real sensors aren't
perfect" treatment WheelSpeedSensor already gets for wheel speed.
"""

import random

from ..specs import cylinder as cyl_specs
from ..specs import exhaust as specs


class OxygenSensor:
    def __init__(self):
        self.lambda_reading = 1.0

    def step(self, dt, actual_afr):
        actual_lambda = actual_afr / cyl_specs.STOICHIOMETRIC_AFR
        alpha = dt / (specs.O2_SENSOR_RESPONSE_TAU_S + dt)
        self.lambda_reading += alpha * (actual_lambda - self.lambda_reading)
        return self.lambda_reading + random.gauss(0.0, specs.O2_SENSOR_NOISE_STD_LAMBDA)
