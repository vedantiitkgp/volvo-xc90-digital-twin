"""Runs a DriveCycle through a full Simulation and produces a usage report."""

from ..sim import Simulation
from .driver_model import DriverModel
from .logger import TripLogger

DEFAULT_DT = 0.02  # 50 Hz — plenty for a multi-minute trip; use 0.002 for launch-transient studies


def run_drive_cycle(cycle, dt=DEFAULT_DT, origin_latlon=None):
    """origin_latlon: real (lat, lon) for a live-routed trip's actual
    geocoded start address (see live_routing.build_drive_cycle_from_addresses)
    — gives the sim's GPS a real live position fix for this run. None (the
    default, and what every synthetic/non-routed drive cycle passes) means
    no GPS fix at all, same as a real receiver that hasn't been given a
    reference point."""
    sim = Simulation()
    if origin_latlon is not None:
        sim.set_gps_origin(*origin_latlon)
    driver = DriverModel()
    logger = TripLogger(sim.can_bus)

    # Starts with the ignition off (see Ignition) and in Park (see
    # GearSelector) — brake, start the engine, wait for cranking to finish,
    # then shift to Drive, same sequence a real driver follows.
    sim.set_driver_inputs(throttle=0.0, brake=1.0)
    sim.start_engine()
    while not sim.ignition.engine_running:
        sim.step(dt)
    sim.set_gear_selector("D")

    t = 0.0
    while t < cycle.duration_s:
        target_speed = cycle.target_speed_mps(t)
        throttle, brake = driver.control(target_speed, sim.body.speed_mps, dt)
        sim.set_driver_inputs(throttle, brake)
        sim.step(dt)
        t += dt

    return logger.report(sim.body.distance_m, sim.time_s)
