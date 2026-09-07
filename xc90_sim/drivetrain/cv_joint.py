"""
CV (constant-velocity) joint: one per front half-shaft — driven AND
steered wheels need these to transmit power through a changing steering
angle. Real wear item (a torn boot loses grease, accelerating wear); a
small efficiency loss at high operating (steering) angle is real but
genuinely tiny at typical street steering angles — modeled as a modest,
bounded derating, not exaggerated.
"""

# ASSUMPTION: real CV joint efficiency loss at operating angle is small
# (a percent or two at typical steering angles) for this class of joint.
MAX_ANGLE_EFFICIENCY_LOSS_FRAC = 0.03
MAX_WEAR_EFFICIENCY_LOSS_FRAC = 0.02


class CVJoint:
    def __init__(self, condition=1.0):
        self.condition = condition

    def efficiency(self, steer_angle_rad):
        angle_loss = min(MAX_ANGLE_EFFICIENCY_LOSS_FRAC, abs(steer_angle_rad) * 0.05)
        wear_loss = (1.0 - self.condition) * MAX_WEAR_EFFICIENCY_LOSS_FRAC
        return 1.0 - angle_loss - wear_loss
