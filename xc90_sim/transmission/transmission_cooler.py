"""
Transmission cooler: real named part rejecting torque-converter slip heat
to ambient air -- reified out of TransmissionFluid's previous fixed
per-Kelvin dissipation constant into its own airflow-dependent object,
the same "effectiveness genuinely depends on airflow" pattern already
used for the engine's radiator (see xc90_sim.cooling.CoolingSystem). Most
passenger-car transmission coolers are small air-cooled heat exchangers
with no fan of their own (unlike the engine radiator) -- no fan-assisted
stationary floor here, just a small natural-convection one.
"""

from ..specs import transmission as specs


class TransmissionCooler:
    def dissipation_w_per_k(self, vehicle_speed_mps):
        speed_frac = min(1.0, abs(vehicle_speed_mps) / specs.TRANS_COOLER_RAM_AIR_SATURATION_MPS)
        return specs.TRANS_COOLER_MIN_DISSIPATION_W_PER_K + speed_frac * (
            specs.TRANS_COOLER_MAX_DISSIPATION_W_PER_K - specs.TRANS_COOLER_MIN_DISSIPATION_W_PER_K
        )
