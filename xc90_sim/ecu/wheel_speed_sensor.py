"""
Wheel speed sensor: quantizes true wheel speed to whole reluctor-ring pulses
per sample window and adds small measurement noise, rather than reporting
the physics engine's exact omega. This is why real ABS/TCS/ESC systems are
unreliable below a few kph — few pulses occur in a short sample window at
low speed, so quantization error dominates.
"""

import math
import random

from ..specs import sensors as specs


class WheelSpeedSensor:
    def __init__(self, sample_period_s):
        self.sample_period_s = sample_period_s
        self._pulse_angle_rad = 2.0 * math.pi / specs.WHEEL_SPEED_SENSOR_PULSES_PER_REV

    def sense_omega_rad_s(self, true_omega_rad_s):
        angle_this_period = true_omega_rad_s * self.sample_period_s
        quantized_pulses = round(angle_this_period / self._pulse_angle_rad)
        quantized_omega = (quantized_pulses * self._pulse_angle_rad) / self.sample_period_s
        noisy_omega = quantized_omega + random.gauss(0.0, specs.WHEEL_SPEED_SENSOR_NOISE_STD_RAD_S)
        return max(0.0, noisy_omega)
