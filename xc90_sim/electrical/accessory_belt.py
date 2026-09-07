"""
Accessory (serpentine) belt: drives the alternator (and, when its clutch
engages, the AC compressor) from crank rotation. This car has ELECTRIC
power-assisted steering (see specs/steering.py) — there is no belt-driven
hydraulic steering pump, unlike older Volvos.

condition (0..1, from WearModel.condition("accessory_belt")) is tracked
for maintenance-due purposes (see wear/wear_model.py — floor_condition is
1.0, same reasoning as the timing belt: it doesn't gradually degrade
performance the way tires/brakes do), and feeds a small real efficiency
effect into the alternator (a worn/slipping belt transmits power less
efficiently) — see Alternator.load_torque_nm().
"""


class AccessoryBelt:
    def __init__(self, condition=1.0):
        self.condition = condition
