"""Full-throttle standing-start acceleration test, for sanity-checking the powertrain model."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xc90_sim.sim import Simulation

DT = 0.002  # 500 Hz fixed-step integration
MAX_TIME_S = 20.0


def main():
    sim = Simulation()
    # Starts with the ignition off (see Ignition) and in Park (see
    # GearSelector) — brake, start the engine, wait for cranking to finish,
    # then shift to Drive, same sequence a real driver follows, before
    # flooring the throttle.
    sim.set_driver_inputs(throttle=0.0, brake=1.0)
    sim.start_engine()
    while not sim.ignition.engine_running:
        sim.step(DT)
    sim.set_gear_selector("D")
    sim.set_driver_inputs(throttle=1.0, brake=0.0)
    launch_start_s = sim.time_s  # exclude ignition/crank time from the 0-60/1/4-mile clock

    last_gear = sim.transmission.gear
    hit_60 = None
    hit_quarter_mile = None

    while sim.time_s < launch_start_s + MAX_TIME_S:
        sim.step(DT)
        t = sim.telemetry()
        elapsed_s = t["time_s"] - launch_start_s

        if t["gear"] != last_gear:
            print(f"t={elapsed_s:5.2f}s  shift -> gear {t['gear']}  "
                  f"({t['engine_rpm']:.0f} rpm, {t['speed_mph']:.1f} mph)")
            last_gear = t["gear"]

        if hit_60 is None and t["speed_mph"] >= 60.0:
            hit_60 = elapsed_s
            print(f"\n0-60 mph: {hit_60:.2f} s\n")

        if hit_quarter_mile is None and t["distance_m"] >= 402.336:
            hit_quarter_mile = elapsed_s
            print(f"1/4 mile: {hit_quarter_mile:.2f} s @ {t['speed_mph']:.1f} mph\n")

        if hit_60 is not None and hit_quarter_mile is not None:
            break

    if hit_60 is None:
        print("Did not reach 60 mph within", MAX_TIME_S, "s")


if __name__ == "__main__":
    main()
