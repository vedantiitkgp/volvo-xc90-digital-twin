"""
Electric coolant (water) pump: this engine uses one (genuine Volvo part
32382249, see xc90_sim/parts_catalog) rather than a belt-driven mechanical
pump, letting the ECU vary coolant flow independently of engine rpm.

Real strategy modeled: near-zero flow during cold start (lets the engine
reach operating temperature faster) ramping to full flow as coolant warms
or under high load; continues running briefly after a hot shutdown to
prevent local boiling around the turbo ("heat soak" protection, a real
feature of electric pumps on turbocharged engines). A `failed` flag gives
this a genuine failure mode -- zero coolant flow regardless of demand,
the real "overheats even standing still with the fan running" symptom of
a dead water pump (distinct from CoolingSystem's radiator/fan, which
still "work" but have nothing moving through them to reject).
"""

from ..specs import cooling as specs


class WaterPump:
    def __init__(self):
        self.flow_frac = 0.0
        self.failed = False
        self._post_shutdown_elapsed_s = 0.0

    def set_failed(self, failed):
        self.failed = failed

    def step(self, dt, coolant_temp_c, engine_running, high_load):
        if self.failed:
            self.flow_frac = 0.0
            return

        if engine_running:
            self._post_shutdown_elapsed_s = 0.0
            if high_load or coolant_temp_c >= specs.WATER_PUMP_FULL_FLOW_C:
                target_frac = 1.0
            elif coolant_temp_c <= specs.WATER_PUMP_WARMUP_START_C:
                target_frac = specs.WATER_PUMP_MIN_WARMUP_FLOW_FRAC
            else:
                span = specs.WATER_PUMP_FULL_FLOW_C - specs.WATER_PUMP_WARMUP_START_C
                frac_through = (coolant_temp_c - specs.WATER_PUMP_WARMUP_START_C) / span
                target_frac = (specs.WATER_PUMP_MIN_WARMUP_FLOW_FRAC
                                + frac_through * (1.0 - specs.WATER_PUMP_MIN_WARMUP_FLOW_FRAC))
        elif (coolant_temp_c >= specs.WATER_PUMP_POST_SHUTDOWN_MIN_TEMP_C
                and self._post_shutdown_elapsed_s < specs.WATER_PUMP_POST_SHUTDOWN_RUN_S):
            target_frac = 1.0
            self._post_shutdown_elapsed_s += dt
        else:
            target_frac = 0.0

        alpha = dt / (specs.WATER_PUMP_RESPONSE_TAU_S + dt)
        self.flow_frac += alpha * (target_frac - self.flow_frac)
