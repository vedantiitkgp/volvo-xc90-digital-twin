"""
Top-level simulation orchestrator: wires engine -> torque converter ->
transmission -> Haldex AWD -> per-axle open differentials -> 4 wheels
(nonlinear tire model) -> 3-DOF vehicle body (longitudinal + lateral + yaw +
world pose) each tick.

Each subsystem is an independently testable/swappable component (see
xc90_sim.engine, xc90_sim.transmission, xc90_sim.drivetrain, xc90_sim.electrical,
xc90_sim.fuel_system, xc90_sim.cooling, xc90_sim.exhaust, xc90_sim.chassis,
xc90_sim.suspension, xc90_sim.steering); this module only owns the sequencing
between them, not any physics of its own.

Numerical note: to avoid solving the driveline as one simultaneous system of
equations, each tick uses the PREVIOUS tick's wheel speeds/body state to
derive the transmission input (turbine) speed, AWD slip, and suspension load
transfer. At the small fixed timestep used here this explicit lag is
negligible; it is the same technique used to break the engine/converter
algebraic loop (see Engine.step_unlocked's capacity-factor pump load, which
depends only on engine speed).
"""

import math

import numpy as np

from ..engine import Engine
from ..transmission import TorqueConverter, Transmission, GearSelector, TransmissionFluid, TransmissionCooler
from ..drivetrain import HaldexAWD, OpenDifferential, Propshaft, CVJoint, WheelBearing
from ..electrical import AutoStopStart, Battery, RelayBox, FuseBox
from ..fuel_system import FuelTank
from ..cooling import CoolingSystem, WaterPump
from ..exhaust import ExhaustSystem
from ..chassis import VehicleBody, Wheel, Brakes, VacuumPump, BrakeBooster
from ..suspension import RideModel, kinematics
from ..steering import SteeringSystem
from ..body import Closures, Windows, Mirrors, Lighting, Ignition, Wipers, Sunroof, Horn, WasherFluid
from ..cabin import HVAC, ParkingAssist, Infotainment, Seating, Storage, SteeringWheelControls, PedalInputs, \
    CruiseController, BlindSpotMonitor, ParkAssistPilot, TPMS, OilLifeMonitor, AirbagSystem, \
    ForwardRadar, AdaptiveCruiseController, LaneCamera, LaneKeepingAssist, GPS
from ..network import CANBus
from ..ecu import EngineECU, TransmissionECU, ChassisECU, AWDECU, BodyECU, CabinECU
from ..dsc import TractionControl, ABS, ESC
from ..wear import WearModel
from ..specs import suspension as suspension_specs
from ..specs import chassis as chassis_specs
from ..specs import transmission as transmission_specs
from ..specs import steering as steering_specs
from ..specs import engine as engine_specs
from ..specs import cabin as cabin_specs
from ..specs import cylinder as cylinder_specs
from ..specs import accessories as accessories_specs
from ..specs import vehicle_identity


class Simulation:
    def __init__(self, mileage=None):
        """
        mileage: odometer reading to evaluate wear at (default: the real
        car's latest known CARFAX reading, specs.service_history.CURRENT_MILEAGE).
        Pass e.g. mileage=0 to simulate this same car showroom-new.
        """
        # Pure metadata identifying the specific real car this models — no
        # physics reads this. See xc90_sim.specs.vehicle_identity.
        self.vehicle_identity = vehicle_identity

        # Wear model: degrades relevant physics constants to match this car's
        # actual condition at the given mileage, from its real service
        # history — see xc90_sim.wear. Update specs/service_history.py to
        # reflect a new real repair; nothing else needs to change.
        self.wear = WearModel(current_mileage=mileage)

        self.engine = Engine(
            condition=self.wear.condition("engine_general"),
            timing_belt_condition=self.wear.condition("timing_belt"),
            accessory_belt_condition=self.wear.condition("accessory_belt"),
        )
        # Real fuel consumption, drawn from the engine's actual cylinder-
        # level fuel injection (Engine.total_fuel_burned_kg) rather than an
        # estimated MPG figure -- see step()'s fuel-tank bookkeeping.
        self.fuel_tank = FuelTank()
        self._last_fuel_burned_kg = 0.0
        # Real coolant temperature from real fuel energy input -- see
        # step()'s cooling-system bookkeeping. Feeds HVAC's cabin heating.
        self.cooling_system = CoolingSystem(initial_coolant_temp_c=20.0)
        # Real electric coolant pump (see xc90_sim.cooling.WaterPump) --
        # radiator rejection now depends on genuine coolant flow, not just
        # airflow; a failed pump is a real, connected overheat failure mode.
        self.water_pump = WaterPump()
        self.converter = TorqueConverter()
        self.transmission = Transmission()
        # Real ATF temperature, heated by genuine torque converter slip
        # loss (see step()'s bookkeeping) rather than assumed constant.
        self.transmission_fluid = TransmissionFluid(condition=self.wear.condition("transmission_fluid"))
        self.transmission_cooler = TransmissionCooler()
        # PRND selector: changes ONLY on an explicit set_gear_selector() call
        # (never automatically) — see xc90_sim.transmission.GearSelector. The
        # transmission's own 1-8 forward-gear shifting is unaffected; this
        # only decides which of P/R/N/D's very different driveline paths
        # step() takes — see step()'s gear_position branch.
        self.gear_selector = GearSelector()
        # Engine Auto Start/Stop: shuts the engine off at a stop to save
        # fuel, then restarts automatically — distinct from the ignition
        # itself (see Ignition below), which stays fully on throughout.
        self.auto_stop_start = AutoStopStart()
        self.awd = HaldexAWD()
        self.front_diff = OpenDifferential()
        self.rear_diff = OpenDifferential()
        # Propshaft: real named part connecting the front transfer case to
        # the rear differential — see propshaft.py for why its windup isn't
        # fed back into the torque path yet.
        self.propshaft = Propshaft()
        wheel_bearing_condition = self.wear.condition("wheel_bearings")
        self.wheel_bearings = {corner: WheelBearing(condition=wheel_bearing_condition)
                                for corner in ("fl", "fr", "rl", "rr")}
        self.body = VehicleBody(
            rolling_resistance_scale=WheelBearing(condition=wheel_bearing_condition).rolling_resistance_scale()
        )
        # CV joints: front half-shafts only (this AWD layout's rear axle
        # isn't independently steered).
        cv_condition = self.wear.condition("cv_joints")
        self.cv_joints = {corner: CVJoint(condition=cv_condition) for corner in ("fl", "fr")}
        tire_grip_scale = self.wear.condition("tires")
        self.wheels = {corner: Wheel(grip_scale=tire_grip_scale) for corner in ("fl", "fr", "rl", "rr")}
        self.brakes = Brakes(
            mass_kg=self.body.mass_kg,
            front_pad_condition=self.wear.condition("front_brakes"),
            rear_pad_condition=self.wear.condition("rear_brakes"),
        )
        self.steering = SteeringSystem()
        self.ride = RideModel(bushing_condition=self.wear.condition("suspension_bushings"))

        # Body control module domain: doors, hood, power tailgate, central
        # locking. Discrete state/timers, not vehicle-dynamics physics — see
        # xc90_sim.body. Doesn't feed back into anything above; it's along
        # for the ride the same way ECUs are, just with its own actuators.
        self.closures = Closures()
        self.windows = Windows()
        self.mirrors = Mirrors()
        self.lighting = Lighting()
        self.wipers = Wipers()
        self.sunroof = Sunroof()
        self.horn = Horn()
        self.washer_fluid = WasherFluid()
        # Volvo's rotary Start/Stop knob: OFF -> cranking -> RUN. Nothing
        # produces driveline torque or gets accessory power until this
        # reaches RUN/ACCESSORY respectively — see step()'s ignition gate.
        self.ignition = Ignition()
        # 12V (AGM) battery: charges while the alternator's actually
        # supplying power, discharges to cover accessory-only demand or
        # the real current spike a starter motor draws while cranking —
        # including a genuine "too weak to crank" failure mode, see
        # start_engine().
        # Real wear: this car's actual battery age (from service history —
        # no recorded replacement, so age is since manufacture; see
        # xc90_sim.wear.WearModel.age_condition()) scales real usable
        # capacity, same "wear evaluated once at construction" pattern as
        # tire grip/brake pad condition elsewhere.
        battery_condition = self.wear.age_condition("battery_12v")
        self.battery = Battery(capacity_ah=accessories_specs.BATTERY_CAPACITY_AH * battery_condition)
        # Support (auxiliary) battery: this car's real second, smaller
        # battery, specifically buffering the electronics bus through every
        # engine restart so the starter's current draw off the main battery
        # doesn't sag voltage enough to reset the infotainment/instrument
        # cluster — see xc90_sim.electrical.Battery's docstring and
        # specs.SUPPORT_BATTERY_CAPACITY_AH. Routing between the two
        # happens in step() below.
        self.support_battery = Battery(capacity_ah=accessories_specs.SUPPORT_BATTERY_CAPACITY_AH)

        # Relays + fuses: the real named parts this car's electrical system
        # routes high-current circuits through and protects them with — see
        # xc90_sim.electrical.RelayBox/FuseBox. Invisible under normal
        # operation (every relay/fuse just passes through); fault-injection
        # hooks (stuck relay contacts, a forced short) give them a genuine,
        # connected effect rather than being decorative labels.
        self.relay_box = RelayBox()
        self.fuse_box = FuseBox()

        # Brake booster vacuum system: this engine's independent variable
        # valve timing leaves too little manifold vacuum at low rpm for the
        # booster, so a small electric pump tops up a vacuum reservoir
        # instead — see xc90_sim.chassis.VacuumPump/BrakeBooster.
        self.vacuum_pump = VacuumPump()
        self.brake_booster = BrakeBooster()

        # Cabin electronics domain: HVAC (real thermal model), parking
        # sensors, infotainment, seating (occupancy/belts/heating), storage
        # (glove box/console), steering wheel buttons + cruise control,
        # pedal travel, blind-spot monitor — see xc90_sim.cabin. Same as
        # xc90_sim.body: discrete state/timers alongside the vehicle-
        # dynamics physics, not feeding back into it (cruise control is the
        # one exception — see step()).
        self.hvac = HVAC()
        self.parking_assist = ParkingAssist()
        self.infotainment = Infotainment()
        # Real GPS position fix, converted from the vehicle body's own
        # real physics-derived local position — see xc90_sim.cabin.GPS.
        # No fix until a real-world origin is set (see set_gps_origin()).
        self.gps = GPS()
        self.seating = Seating()
        self.airbag_system = AirbagSystem(self.seating)
        self.storage = Storage()
        self.steering_wheel_controls = SteeringWheelControls()
        self.pedals = PedalInputs()
        self.blind_spot_monitor = BlindSpotMonitor()
        # Semi-autonomous parallel parking: scans for a gap with a side
        # sensor, then steers itself through the maneuver once engaged in
        # Reverse — a genuine steering-angle override, not just a warning
        # layer. See step() for how it takes over self.steering and a slow
        # auto-creep throttle/brake while maneuvering.
        self.park_assist_pilot = ParkAssistPilot()
        self.tpms = TPMS()
        # Miles-since-reset countdown, not a literal oil-quality sensor —
        # see xc90_sim.cabin.OilLifeMonitor. Fed real distance each tick
        # from self.body.distance_m (see step()).
        self.oil_life_monitor = OilLifeMonitor()
        self._last_distance_m = 0.0
        self._cruise_controller = CruiseController()
        # Radar-based ADAS: Adaptive Cruise Control (follow-distance) and
        # lane-keeping steering assist — see xc90_sim.cabin.adaptive_cruise /
        # lane_keeping_assist. Both sensors (ForwardRadar/LaneCamera) are
        # externally-driven virtual sensors, same pattern as BlindSpotMonitor/
        # ParkingAssist, since this project has no real traffic/lane sim.
        self.forward_radar = ForwardRadar()
        self.adaptive_cruise = AdaptiveCruiseController()
        self.lane_camera = LaneCamera()
        self.lane_keeping_assist = LaneKeepingAssist()
        self.outside_temp_c = 20.0
        self._manual_throttle = 0.0
        self._manual_brake = 0.0
        self._manual_steering_deg = 0.0
        self.engine_removed = False  # physical teardown state -- see set_engine_removed()

        # CAN bus + ECUs: an observational layer that reports live sim state
        # as byte-packed CAN frames on a schedule, same as a real vehicle
        # network — it doesn't feed back into the physics above.
        self.can_bus = CANBus()
        self.ecus = [
            EngineECU(self.can_bus, self.engine),
            TransmissionECU(self.can_bus, self.transmission, self.converter, self.wheels),
            ChassisECU(self.can_bus, self.body, self.wheels, self.steering, self.brakes),
            AWDECU(self.can_bus, self.awd),
            BodyECU(self.can_bus, self.closures, self.windows, self.mirrors, self.lighting, self.wipers, self.sunroof),
            CabinECU(
                self.can_bus, self.hvac, self.parking_assist, self.infotainment, self.seating,
                self.blind_spot_monitor, self.body, self.tpms, self.oil_life_monitor, self.fuel_tank,
            ),
        ]

        # DSTC (Volvo's traction/stability control): senses over the CAN bus
        # like a real module would, actuates by cutting engine torque
        # (TractionControl), releasing per-wheel brake torque (ABS), or
        # adding single-wheel corrective braking the driver never asked for
        # (ESC, for understeer/oversteer).
        self.traction_control = TractionControl(self.can_bus)
        self.abs = ABS(self.can_bus)
        self.esc = ESC(self.can_bus)

        self.time_s = 0.0

    def set_driver_inputs(self, throttle, brake):
        """Manual pedal input. Ignored for throttle while cruise control is engaged (see
        step()) — pressing the brake, though, always cancels cruise, same as a real car."""
        self._manual_throttle = throttle
        self._manual_brake = brake
        if brake > 0.05 and self.steering_wheel_controls.cruise_control_engaged:
            self.steering_wheel_controls.press_cruise_cancel()

    def set_traction_control_enabled(self, enabled):
        """Some cars let the driver disable TCS (e.g. a sport/off mode). ABS cannot be disabled."""
        self.traction_control.set_enabled(enabled)

    def set_steering_wheel_angle_deg(self, angle_deg):
        """Manual steering input. Overridden in step() while Park Assist
        Pilot is actively maneuvering — same as pressing the gas or brake
        pedal doesn't fight cruise control, turning the wheel doesn't fight
        the pilot's own steering command."""
        self._manual_steering_deg = angle_deg

    def set_transmission_mode(self, mode):
        """mode: 'auto' or 'manual' (Geartronic tip-shift)."""
        self.transmission.set_mode(mode)

    def request_upshift(self):
        self.transmission.request_upshift()

    def request_downshift(self):
        self.transmission.request_downshift()

    def set_door(self, corner, open_):
        """corner: 'fl'/'fr'/'rl'/'rr'. Manual entry/exit, not the power tailgate."""
        self.closures.set_door(corner, open_)

    def set_hood(self, open_):
        self.closures.set_hood(open_)

    def request_tailgate(self, open_):
        """Power tailgate: takes real seconds to open/close, not instant — see Closures.step."""
        self.closures.request_tailgate(open_)

    def lock_doors(self):
        self.closures.lock()
        if self.closures.locked:
            self.mirrors.set_folded(True)  # real, common feature: mirrors fold on central lock

    def unlock_doors(self):
        self.closures.unlock()
        self.mirrors.set_folded(False)

    def unlock_driver_door_only(self):
        """Real single-stage remote-unlock behavior — see Closures.unlock_driver_only()."""
        self.closures.unlock_driver_only()
        self.mirrors.set_folded(False)

    def set_gear_selector(self, position):
        """position: 'P'/'R'/'N'/'D'. The ONLY way this ever changes — nothing
        in this simulation shifts P/R/N/D on its own. Returns True if honored,
        False if a real safety interlock blocked it (see GearSelector) — e.g.
        requesting 'D' from 'P' without the brake pedal pressed."""
        honored = self.gear_selector.request(position, self._manual_brake, self.body.speed_mps)
        if honored and position != "D" and self.steering_wheel_controls.cruise_control_engaged:
            self.steering_wheel_controls.press_cruise_cancel()  # cruise only makes sense in Drive
        return honored

    def start_engine(self):
        """Turns the rotary knob to crank. Returns False if the brake-to-start
        interlock blocked it (brake pedal not pressed — see Ignition), if
        the battery is too weak (or disconnected) to crank, or if the
        engine itself has been physically removed — all real, connected
        failure modes, not just a dashboard warning with no consequence."""
        if self.engine_removed or not self.battery.can_crank():
            return False
        return self.ignition.rotate_to_start(self._manual_brake)

    def stop_engine(self):
        self.ignition.push_to_stop()

    def set_engine_removed(self, removed):
        """Physically pull/reinstall the engine — the most drastic teardown
        state: no ignition/starter attempt can ever produce torque while
        this is set, regardless of battery/fuel/everything else."""
        self.engine_removed = removed

    def set_battery_disconnected(self, disconnected):
        self.battery.set_disconnected(disconnected)

    def pull_fuse(self, name):
        self.fuse_box.pull(name)

    def replace_fuse(self, name):
        self.fuse_box.replace(name)

    def disconnect_relay(self, name):
        """Simulates pulling a relay out of its socket — same effect as a
        stuck-open fault (see RelayBox), reusing that mechanism directly."""
        self.relay_box.set_stuck_open(name, True)

    def reconnect_relay(self, name):
        self.relay_box.clear_fault(name)

    def set_accessory_power(self):
        """Partial turn: infotainment/HVAC available, engine not running."""
        self.ignition.to_accessory()

    def start_park_pilot_scan(self, side):
        """side: 'left' or 'right' — which side to scan for a gap while driving past."""
        self.park_assist_pilot.start_scanning(side)

    def set_park_pilot_side_obstacle_m(self, distance_m):
        """distance_m: None if nothing detected within sensor range (a gap)."""
        self.park_assist_pilot.set_side_obstacle_distance_m(distance_m)

    def engage_park_pilot(self):
        """Starts the actual steering maneuver. Requires Reverse — same as
        the real feature, which only steers while backing into the spot.
        Returns False if not in Reverse or no gap has been found yet."""
        if self.gear_selector.position != "R":
            return False
        return self.park_assist_pilot.engage(self.body.heading_rad)

    def cancel_park_pilot(self):
        """The driver taking back control — honored at any phase, any time."""
        self.park_assist_pilot.cancel()

    def request_window(self, corner, target_pct):
        """corner: 'fl'/'fr'/'rl'/'rr'. target_pct: 0 (closed) .. 100 (fully open)."""
        self.windows.request_position(corner, target_pct)

    def set_headlight_mode(self, mode):
        """mode: 'off'/'parking'/'low_beam'/'high_beam'."""
        self.lighting.set_headlight_mode(mode)

    def set_indicator(self, side):
        """side: None (cancel), 'left', or 'right'."""
        self.lighting.set_indicator(side)

    def set_hazards(self, on):
        self.lighting.set_hazards(on)

    def set_fog_lights(self, on):
        self.lighting.set_fog_lights(on)

    def set_dome_light_override(self, on):
        self.lighting.set_dome_light_override(on)

    def set_honking(self, honking):
        self.horn.set_honking(honking)

    def spray_washer_fluid(self):
        """No-ops (silently, same as a real dry reservoir) if empty."""
        self.washer_fluid.spray()

    def refill_washer_fluid(self):
        self.washer_fluid.refill()

    def set_front_wiper_speed(self, speed):
        """speed: 'off'/'intermittent'/'low'/'high'."""
        self.wipers.set_front_speed(speed)

    def set_rear_wiper_speed(self, speed):
        """speed: 'off'/'intermittent'/'on'."""
        self.wipers.set_rear_speed(speed)

    def request_sunroof_glass(self, state):
        """state: 'closed'/'vent'/'open'. Opening auto-opens the shade first
        (a real mechanical interlock) — see Sunroof."""
        self.sunroof.request_glass(state)

    def request_sunroof_shade(self, open_):
        """No-ops if the glass isn't fully closed — see Sunroof."""
        self.sunroof.request_shade(open_)

    def set_seat_folded_flat(self, seat_name, folded):
        """No-ops for front seats — only 2nd/3rd row actually fold flat, see Seat.can_fold_flat."""
        self.seating.seats[seat_name].set_folded_flat(folded)

    def set_auto_stop_start_enabled(self, enabled):
        """Dash toggle, same as a real car — driver can disable Auto Start/Stop per trip."""
        self.auto_stop_start.set_enabled(enabled)

    def set_left_blind_spot_occupied(self, occupied):
        self.blind_spot_monitor.set_left_occupied(occupied)

    def set_right_blind_spot_occupied(self, occupied):
        self.blind_spot_monitor.set_right_occupied(occupied)

    def set_lead_vehicle(self, distance_m, relative_speed_mps):
        """Forward radar virtual sensor for Adaptive Cruise Control — see
        xc90_sim.cabin.ForwardRadar. No real traffic sim exists in this
        project, so a lead vehicle's distance/relative speed is set from
        outside, same pattern as blind-spot occupancy above."""
        self.forward_radar.set_lead_vehicle(distance_m, relative_speed_mps)

    def clear_lead_vehicle(self):
        self.forward_radar.clear_lead_vehicle()

    def set_acc_follow_gap(self, setting):
        self.adaptive_cruise.set_follow_gap(setting)

    def set_water_pump_failed(self, failed):
        """Fault-injection hook, same pattern as Relay/Fuse -- a dead
        electric coolant pump means zero coolant flow regardless of
        demand, a real, severe overheat failure mode."""
        self.water_pump.set_failed(failed)

    def set_lane_state(self, detected, lateral_offset_m=0.0, heading_error_rad=0.0):
        """Forward camera virtual sensor for lane-keeping assist — see
        xc90_sim.cabin.LaneCamera. Same external-sensor pattern as above."""
        self.lane_camera.set_lane_state(detected, lateral_offset_m, heading_error_rad)

    def set_lane_keeping_assist_enabled(self, enabled):
        """Dash/steering-wheel toggle, same as a real car's Pilot Assist steering switch."""
        self.lane_keeping_assist.set_enabled(enabled)

    def set_head_restraint_up(self, seat_name, up):
        self.seating.seats[seat_name].set_head_restraint_up(up)

    def set_glove_box(self, open_):
        self.storage.set_glove_box(open_)

    def set_center_console(self, open_):
        self.storage.set_center_console(open_)

    def set_tire_pressure_psi(self, corner, psi):
        self.tpms.set_pressure_psi(corner, psi)

    def reset_oil_life(self):
        """The service-menu action a technician performs after an actual oil change."""
        self.oil_life_monitor.reset()

    def add_fuel_l(self, liters, ethanol_fraction=None, octane_aki=None):
        """Refueling. Optionally specify what grade/blend was pumped —
        defaults to whatever's already in the tank (topping off with "the
        same stuff") — see FuelTank.add_fuel_l()."""
        self.fuel_tank.add_fuel_l(liters, ethanol_fraction, octane_aki)

    def set_gps_origin(self, lat, lon):
        """Real-world lat/lon for the vehicle body's local (0, 0) — pass
        the trip's actual geocoded start address (see
        xc90_sim.trip.live_routing.geocode()) for a real live position
        fix during a routed trip."""
        self.gps.set_origin(lat, lon)

    def set_gps_signal_lost(self, lost):
        """Fault-injection hook — tunnels, parking garages, dense urban
        canyons, same pattern as Relay/Fuse."""
        self.gps.set_signal_lost(lost)

    def set_infotainment_screen(self, screen):
        """screen: one of Infotainment.SCREENS ('home'/'media'/'nav'/'climate'/
        'park_assist'/'seats'/'car_status') — real touchscreen menu navigation."""
        self.infotainment.set_screen(screen)

    def infotainment_screen_data(self):
        """What the current infotainment screen would actually show — composes
        whichever subsystem's status is relevant to Infotainment.current_screen,
        without coupling Infotainment itself to HVAC/ParkingAssist/Seating/etc.
        (same "compose at the Simulation level" pattern as active_park_zone())."""
        screen = self.infotainment.current_screen
        if screen == "climate":
            return {
                "power_on": self.hvac.power_on,
                "cabin_temp_c": self.hvac.cabin_temp_c,
                "target_temp_c": self.hvac.target_temp_c,
                "fan_speed": self.hvac.fan_speed,
                "ac_enabled": self.hvac.ac_enabled,
            }
        if screen == "park_assist":
            return {
                "front_zone": self.parking_assist.front_zone(),
                "rear_zone": self.parking_assist.rear_zone(),
                "active_zone": self.active_park_zone(),
                "pilot_phase": self.park_assist_pilot.phase,
                "pilot_gap_length_m": self.park_assist_pilot.found_gap_length_m,
            }
        if screen == "seats":
            return {
                name: {
                    "occupied": seat.occupied,
                    "seatbelt_buckled": seat.seatbelt_buckled,
                    "heating_level": seat.heating_level,
                    "folded_flat": seat.folded_flat,
                    "head_restraint_up": seat.head_restraint_up,
                }
                for name, seat in self.seating.seats.items()
            }
        if screen == "car_status":
            return {
                "oil_life_pct": round(self.oil_life_monitor.life_pct(), 1),
                "oil_change_due": self.oil_life_monitor.change_due(),
                "tire_pressures_psi": dict(self.tpms.pressures_psi),
                "tire_pressure_warning": self.tpms.any_warning(),
                "fuel_level_l": round(self.fuel_tank.level_l, 1),
                "low_fuel_warning": self.fuel_tank.low_fuel_warning(),
            }
        return {}

    def set_outside_temp_c(self, temp_c):
        self.outside_temp_c = temp_c

    def set_hvac_power(self, on):
        self.hvac.set_power(on)

    def set_hvac_target_temp_c(self, temp_c):
        self.hvac.set_target_temp_c(temp_c)

    def set_hvac_fan_speed(self, level):
        self.hvac.set_fan_speed(level)

    def set_front_park_obstacle_m(self, distance_m):
        self.parking_assist.set_front_obstacle_distance_m(distance_m)

    def set_rear_park_obstacle_m(self, distance_m):
        self.parking_assist.set_rear_obstacle_distance_m(distance_m)

    def active_park_zone(self):
        """Real park-assist UX shows rear sensors while reversing ('park in') and
        front sensors while in Drive ('park out'), not both at once — ParkingAssist
        itself doesn't know about gear (kept standalone/testable), so this composes
        the two rather than pushing gear awareness down into that class."""
        position = self.gear_selector.position
        if position == "R":
            return self.parking_assist.rear_zone()
        if position == "D":
            return self.parking_assist.front_zone()
        return "none"

    def press_cruise_set(self):
        """Engages cruise control at the current speed, same as a real "SET" button press.
        No-ops outside Drive — a real car doesn't let you set cruise in Park/Reverse/Neutral."""
        if self.gear_selector.position != "D":
            return
        self.steering_wheel_controls.press_cruise_set(self.body.speed_mps * 3.6)

    def press_cruise_resume(self):
        if self.gear_selector.position != "D":
            return
        self.steering_wheel_controls.press_cruise_resume()

    def press_cruise_cancel(self):
        self.steering_wheel_controls.press_cruise_cancel()

    def adjust_cruise_speed_kph(self, delta_kph):
        self.steering_wheel_controls.adjust_cruise_speed_kph(delta_kph)

    def set_seat_occupied(self, seat_name, occupied):
        self.seating.seats[seat_name].set_occupied(occupied)

    def set_seatbelt_buckled(self, seat_name, buckled):
        self.seating.seats[seat_name].set_seatbelt_buckled(buckled)

    def set_child_seat_installed(self, seat_name, installed):
        """Occupant Classification System input — a detected child seat
        suppresses that seat's frontal airbag even while occupied."""
        self.seating.seats[seat_name].set_child_seat_installed(installed)

    def set_srs_self_test_fault(self, fault):
        """SRS fault-injection hook (buckle-switch continuity, clockspring,
        etc.) — lights the SRS warning independent of any deployment."""
        self.airbag_system.set_self_test_fault(fault)

    def set_seat_heating_level(self, seat_name, level):
        self.seating.seats[seat_name].set_heating_level(level)

    def _front_diff_carrier_omega(self):
        # An ideal open differential's carrier speed is the average of its
        # two output speeds — this is what the transmission/converter side
        # of the driveline actually sees and reacts to.
        return (self.wheels["fl"].omega + self.wheels["fr"].omega) / 2.0

    def _rear_diff_carrier_omega(self):
        return (self.wheels["rl"].omega + self.wheels["rr"].omega) / 2.0

    def step(self, dt):
        # -1. Ignition: OFF -> cranking -> RUN. Nothing downstream produces
        #     driveline torque, or gets accessory power, until this says so.
        self.ignition.step(dt)
        if not self.ignition.accessory_power:
            self.infotainment.set_power(False)
            self.hvac.set_power(False)

        # -0.5. Real electrical demand from whatever's actually switched on
        #       right now, feeding the alternator's genuine crank-torque
        #       draw (see Engine._accessory_load_torque_nm) — turning on
        #       headlights/HVAC fan/heated seats really does load the
        #       engine now, not a single made-up constant regardless of
        #       what's on.
        # Relays: energize each one from the real signal that should
        # control it this tick — invisible unless a fault's been injected
        # (see xc90_sim.electrical.RelayBox), in which case contacts_closed
        # can diverge from energized (stuck open/closed).
        self.relay_box.set_energized("cooling_fan", self.cooling_system.fan_on)
        self.relay_box.set_energized("horn", self.horn.honking)
        self.relay_box.set_energized("main_ecu", self.ignition.accessory_power)
        cooling_fan_relay_closed = self.relay_box.contacts_closed("cooling_fan")
        horn_relay_closed = self.relay_box.contacts_closed("horn")

        electrical_demand_w = 0.0
        headlight_w = 0.0
        if self.lighting.headlight_mode == "low_beam":
            headlight_w = accessories_specs.HEADLIGHT_LOW_BEAM_W
        elif self.lighting.headlight_mode == "high_beam":
            headlight_w = accessories_specs.HEADLIGHT_LOW_BEAM_W + accessories_specs.HEADLIGHT_HIGH_BEAM_W
        elif self.lighting.headlight_mode == "parking":
            headlight_w = accessories_specs.PARKING_LIGHT_W
        self.fuse_box.check("headlights", headlight_w / accessories_specs.BATTERY_NOMINAL_VOLTAGE)
        if not self.fuse_box.is_blown("headlights"):
            electrical_demand_w += headlight_w
        if self.lighting.drl_on(self.ignition.engine_running):
            electrical_demand_w += accessories_specs.DRL_W
        if self.hvac.power_on:
            electrical_demand_w += accessories_specs.HVAC_BLOWER_MAX_W * (self.hvac.fan_speed / cabin_specs.MAX_FAN_SPEED)
        for seat in self.seating.seats.values():
            if seat.has_heating and seat.heating_level > 0:
                electrical_demand_w += accessories_specs.SEAT_HEATER_MAX_W * (seat.heating_level / cabin_specs.SEAT_HEAT_LEVELS)
        infotainment_w = accessories_specs.INFOTAINMENT_W if self.infotainment.power_on else 0.0
        self.fuse_box.check("infotainment", infotainment_w / accessories_specs.BATTERY_NOMINAL_VOLTAGE)
        if not self.fuse_box.is_blown("infotainment"):
            electrical_demand_w += infotainment_w
        wiper_w = accessories_specs.WIPER_MOTOR_W if self.wipers.front_speed != "off" else 0.0
        self.fuse_box.check("wipers", wiper_w / accessories_specs.BATTERY_NOMINAL_VOLTAGE)
        if not self.fuse_box.is_blown("wipers"):
            electrical_demand_w += wiper_w
        horn_w = accessories_specs.HORN_W if (self.horn.honking and horn_relay_closed) else 0.0
        self.fuse_box.check("horn", horn_w / accessories_specs.BATTERY_NOMINAL_VOLTAGE)
        if not self.fuse_box.is_blown("horn"):
            electrical_demand_w += horn_w
        if self.lighting.fog_lights_on:
            electrical_demand_w += accessories_specs.FOG_LIGHT_W
        dome_light_w = accessories_specs.DOME_LIGHT_W if self.lighting.dome_light_on else 0.0
        self.fuse_box.check("dome_light", dome_light_w / accessories_specs.BATTERY_NOMINAL_VOLTAGE)
        if not self.fuse_box.is_blown("dome_light"):
            electrical_demand_w += dome_light_w
        # Cooling fan: real electrical draw, gated through its relay — was
        # never actually connected to the electrical system before (see
        # STATUS.md's bugs-found log).
        cooling_fan_w = accessories_specs.COOLING_FAN_ELECTRICAL_W if cooling_fan_relay_closed else 0.0
        self.fuse_box.check("cooling_fan", cooling_fan_w / accessories_specs.BATTERY_NOMINAL_VOLTAGE)
        if not self.fuse_box.is_blown("cooling_fan"):
            electrical_demand_w += cooling_fan_w
        # Brake-booster vacuum pump: real electrical draw while its
        # electric pump is actively running (see xc90_sim.chassis.VacuumPump) —
        # reflects last tick's running state, same explicit-lag pattern as
        # the rest of this tick (the pump itself steps later below, once
        # this tick's actual brake pedal is resolved).
        electrical_demand_w += self.vacuum_pump.electrical_load_w()
        self.engine.set_electrical_demand_w(electrical_demand_w)
        # AC compressor: mechanical (belt), separate from the electrical
        # demand above — engaged only while HVAC is actually calling for
        # active cooling, not just because the AC button is on.
        self.engine.set_ac_compressor_active(
            self.hvac.power_on and self.hvac.ac_enabled and self.hvac.cabin_temp_c > self.hvac.target_temp_c
        )

        # Real fuel chemistry/aging: what's actually in the tank (ethanol
        # content, octane shortfall vs. what this engine wants, staleness
        # from sitting too long) feeds the combustion model for real — see
        # xc90_sim.fuel_system.FuelTank.
        self.fuel_tank.step(dt)
        self.engine.set_fuel_quality(
            self.fuel_tank.effective_lhv_j_per_kg(),
            self.fuel_tank.effective_stoich_afr(),
            self.fuel_tank.octane_boost_derate_frac(),
            cylinder_specs.COMBUSTION_EFFICIENCY * (1.0 - self.fuel_tank.staleness_combustion_derate_frac()),
        )

        # Dual battery: this car's real second (support/auxiliary) battery
        # buffers the electronics bus through every engine restart — not
        # just the very first one — so the starter's big current draw off
        # the MAIN battery doesn't sag voltage enough to reset sensitive
        # electronics (see xc90_sim.electrical.Battery's docstring). An
        # Auto-Stop-Start restart is detected here the same way the
        # driveline branch below detects it (engine running, not auto-
        # stopped, rpm still below idle) — same real event, read in both
        # places rather than duplicating the restart logic itself.
        restarting_from_auto_stop = (
            self.ignition.engine_running and not self.auto_stop_start.engine_auto_stopped
            and self.engine.rpm < engine_specs.IDLE_RPM - 1.0
        )
        cranking_now = self.ignition.state == "cranking" or restarting_from_auto_stop
        self.relay_box.set_energized("starter", cranking_now)
        starter_relay_closed = self.relay_box.contacts_closed("starter")

        if cranking_now:
            self.battery.step(dt, -accessories_specs.CRANKING_DISCHARGE_W if starter_relay_closed else 0.0)
            self.support_battery.step(dt, -electrical_demand_w)
        elif self.ignition.engine_running:
            self.battery.step(dt, accessories_specs.BATTERY_MAINTENANCE_CHARGE_W)
            self.support_battery.step(dt, accessories_specs.SUPPORT_BATTERY_MAINTENANCE_CHARGE_W)
        else:
            self.battery.step(dt, -electrical_demand_w if self.ignition.accessory_power else 0.0)
            self.support_battery.step(dt, 0.0)

        # 0. Traction control: apply the torque cut computed from last tick's
        #    CAN broadcast (wheel speeds, reference speed) before the engine
        #    produces this tick's torque — same explicit-lag pattern as
        #    everything else here.
        self.engine.set_traction_control_limit(self.traction_control.torque_limit_frac())

        # Cruise control cancels itself if TCS or ABS actively intervenes
        # (real cars do this — a slipping/locking wheel means road conditions
        # cruise control shouldn't be blindly holding speed through), if the
        # gear selector isn't in Drive (checked in set_gear_selector() too,
        # but the driver could also lift off after a TCS/ABS event), or if
        # the engine isn't even running.
        if self.steering_wheel_controls.cruise_control_engaged and (
            self.traction_control.is_active() or self.abs.is_active()
            or self.gear_selector.position != "D" or not self.ignition.engine_running
        ):
            self.steering_wheel_controls.press_cruise_cancel()

        # Park Assist Pilot cancels itself on a firm manual brake press
        # (same as cruise control above) or if the gear selector leaves
        # Reverse — a real system hands back control the instant the driver
        # intervenes, rather than continuing a planned maneuver regardless.
        if self.park_assist_pilot.is_maneuvering() and (
            self._manual_brake > 0.5 or self.gear_selector.position != "R"
        ):
            self.park_assist_pilot.cancel()

        # 0.5. Resolve throttle/brake. Priority: Park Assist Pilot's own slow
        #      auto-creep (while actively maneuvering) > cruise control (if
        #      engaged) > manual pedal input. Must resolve before shift
        #      logic (below), which reads self.engine.throttle. Reuses
        #      _cruise_controller for the creep phase too — same generic
        #      speed-tracking technique, and mutually exclusive with actual
        #      cruise control by construction (cruise requires Drive, the
        #      pilot requires Reverse), so sharing one controller instance
        #      is safe.
        if self.park_assist_pilot.is_maneuvering():
            target_mps = -cabin_specs.PARK_PILOT_CREEP_SPEED_MPS
            throttle, brake = self._cruise_controller.control(target_mps, self.body.speed_mps, dt)
        elif (self.steering_wheel_controls.cruise_control_engaged
                and self.steering_wheel_controls.cruise_set_speed_kph is not None):
            driver_set_mps = self.steering_wheel_controls.cruise_set_speed_kph / 3.6
            # Adaptive Cruise Control: when a lead vehicle is detected, this
            # lowers the target speed to hold the selected follow gap —
            # otherwise it's identical to plain cruise control tracking the
            # driver's set speed (see AdaptiveCruiseController.effective_target_speed_mps).
            target_mps = self.adaptive_cruise.effective_target_speed_mps(
                self.forward_radar, driver_set_mps, self.body.speed_mps
            )
            throttle, brake = self._cruise_controller.control(target_mps, self.body.speed_mps, dt)
        else:
            throttle, brake = self._manual_throttle, self._manual_brake

        # Low-speed collision mitigation: connects the parking sensors to
        # the engine/brakes, not just a dashboard tone — a real, if
        # simplified, version of what Volvo's City Safety does at parking
        # speed. Overrides whatever throttle/brake source was chosen above,
        # including manual input — the whole point is it can't be out-
        # throttled by the driver once something's critically close.
        if self.active_park_zone() == "critical":
            throttle = 0.0
            brake = max(brake, cabin_specs.PARK_ASSIST_AUTO_BRAKE_FRAC)

        self.engine.set_throttle(throttle)
        self.brakes.set_pedal(brake)
        # Brake booster vacuum: this tick's actual pedal draws down the
        # reservoir (or the electric pump tops it back up) — see
        # xc90_sim.chassis.VacuumPump/BrakeBooster.
        self.vacuum_pump.step(dt, brake)
        self.pedals.set_accelerator_pct(throttle * 100.0)
        self.pedals.set_brake_pct(brake * 100.0)
        # Real, connected — not driver-settable: brake lights reflect the
        # actual pedal, reverse lights the actual gear selector.
        self.lighting.brake_lights_on = brake > 0.02
        self.lighting.reverse_lights_on = self.gear_selector.position == "R"

        # Steering: Park Assist Pilot overrides the driver's own input while
        # actively maneuvering (turn to lock, then countersteer — see
        # ParkAssistPilot), the same way cruise control overrides pedal
        # input above.
        if self.park_assist_pilot.is_maneuvering():
            commanded_steer_deg = self.park_assist_pilot.steering_command_deg(
                steering_specs.MAX_STEERING_WHEEL_ANGLE_DEG
            )
        else:
            # Lane-keeping assist adds a small, bounded corrective nudge on
            # top of the driver's own steering input — never overrides it
            # the way Park Assist Pilot does above (see LaneKeepingAssist).
            turn_signal_active = self.lighting.indicator is not None
            lka_correction_deg = self.lane_keeping_assist.corrective_steering_deg(
                self.lane_camera, self._manual_steering_deg, turn_signal_active
            )
            commanded_steer_deg = self._manual_steering_deg + lka_correction_deg
        self.steering.set_wheel_angle_deg(commanded_steer_deg)

        # 1. Shift logic runs off an idealized (no-slip) vehicle-speed-derived
        #    wheel speed — the same reason real TCUs key shifts off a VSS
        #    signal rather than the driven wheel's own speed: driven-wheel
        #    speed is corrupted by tire slip (e.g. launch wheelspin), which
        #    would otherwise cause spurious shifts. The torque converter
        #    itself, below, correctly uses the real (slip-including) wheel
        #    speed, since converter/gear speeds genuinely follow the wheel.
        gear_position = self.gear_selector.position
        slip_heat_w = 0.0  # real torque-converter slip loss, set below when unlocked -- feeds TransmissionFluid

        # Engine Auto Start/Stop: decide (using this tick's resolved brake,
        # above) whether the engine should be auto-stopped at this light —
        # distinct from the ignition itself, which stays fully RUN
        # throughout (accessories unaffected either way).
        self.auto_stop_start.step(self.ignition.engine_running, self.body.speed_mps, brake, gear_position)

        if self.engine_removed or not self.ignition.engine_running:
            # No ignition, no driveline — the engine either spins down (off/
            # accessory) or is being cranked by the starter, and either way
            # nothing reaches the wheels. Skips shift logic and torque
            # converter lockup entirely; there's nothing for either to do.
            # engine_removed forces this branch unconditionally: there's
            # physically nothing to crank regardless of ignition state.
            if not self.engine_removed and self.ignition.state == "cranking" and starter_relay_closed:
                self.engine.step_cranking(dt)
            else:
                # Also covers a stuck-open starter relay while "cranking":
                # the real "turn the key, nothing happens" symptom — the
                # starter never actually spins the engine.
                self.engine.step_off(dt)
            self.converter.locked = False
            driveshaft_torque = 0.0

        elif self.auto_stop_start.engine_auto_stopped:
            # Auto-stopped at a light: same "no torque reaches the wheels"
            # outcome as Park/Neutral, but the engine itself is what's off
            # here (ignition/accessories are untouched) — spins down the
            # same way ignition-off does.
            if self.engine.rpm > 0:
                self.engine.step_off(dt)
            self.converter.locked = False
            driveshaft_torque = 0.0

        elif self.engine.rpm < engine_specs.IDLE_RPM - 1.0:
            # Restarting after an auto-stop (the only way rpm ends up below
            # idle while the ignition is RUN and not auto-stopped — both
            # step_locked and step_unlocked otherwise enforce an idle
            # floor) — ramp back up on the much quicker auto-restart
            # timer before resuming normal driveline processing below.
            if starter_relay_closed:
                self.engine.step_cranking(dt, engine_specs.AUTO_STOP_RESTART_TIME_S)
            else:
                self.engine.step_off(dt)
            self.converter.locked = False
            driveshaft_torque = 0.0

        elif gear_position in ("P", "N"):
            # No drive path exists in Park/Neutral: the torque converter's
            # pump is always coupled to the engine (so the engine still
            # idles/revs against it), but the turbine has no wheel coupling
            # and zero torque reaches the driveshaft — same as a real car
            # revving in neutral. Never locks up here (nothing to lock to).
            pump_load = self.converter.pump_load_torque_nm(self.engine.omega)
            self.engine.step_unlocked(dt, pump_load)
            self.converter.locked = False
            driveshaft_torque = 0.0

        elif gear_position == "R":
            # Reverse: a single fixed ratio (no multi-speed shifting), same
            # driveline sequence as Drive otherwise. reverse_ratio's sign
            # does double duty: it keeps the turbine/engine spinning in
            # their one real physical direction (positive rpm) regardless of
            # which way the car is actually moving, AND flips the torque
            # delivered to the wheels negative so the car actually backs up
            # — both fall out of the same signed constant, not separate
            # sign-handling logic. See specs/transmission.py's REVERSE_RATIO.
            reverse_ratio = -transmission_specs.REVERSE_RATIO * transmission_specs.FINAL_DRIVE_RATIO
            ideal_wheel_omega = self.body.speed_mps / chassis_specs.TIRE_ROLLING_RADIUS_M
            ideal_turbine_omega = ideal_wheel_omega * reverse_ratio
            real_turbine_omega = self._front_diff_carrier_omega() * reverse_ratio

            locked = self.converter.update(self.engine.omega, real_turbine_omega, ideal_turbine_omega)
            if locked:
                ideal_turbine_rpm = ideal_turbine_omega * 60.0 / (2.0 * np.pi)
                turbine_torque = self.engine.step_locked(dt, ideal_turbine_rpm)
            else:
                pump_load = self.converter.pump_load_torque_nm(self.engine.omega)
                self.engine.step_unlocked(dt, pump_load)
                turbine_torque = self.converter.turbine_torque_nm(pump_load)
                slip_heat_w = abs(pump_load * self.engine.omega - turbine_torque * real_turbine_omega)
            driveshaft_torque = turbine_torque * reverse_ratio

        else:  # "D"
            ideal_wheel_omega = self.body.speed_mps / chassis_specs.TIRE_ROLLING_RADIUS_M
            ideal_turbine_omega = self.transmission.input_omega(ideal_wheel_omega)
            shift_ref_rpm = ideal_turbine_omega * 60.0 / (2.0 * np.pi)
            self.transmission.step(dt, shift_ref_rpm, self.engine.throttle)

            # The real (slip-including) turbine speed is what the converter's
            # fluid coupling physically sees; the idealized one (above) is
            # only used for control decisions (shifting, lockup) that must
            # be immune to wheelspin — see TorqueConverter's docstring.
            real_turbine_omega = self.transmission.input_omega(self._front_diff_carrier_omega())

            # 2. Torque converter: decide lock state, compute turbine torque.
            locked = self.converter.update(self.engine.omega, real_turbine_omega, ideal_turbine_omega)
            if locked:
                ideal_turbine_rpm = ideal_turbine_omega * 60.0 / (2.0 * np.pi)
                turbine_torque = self.engine.step_locked(dt, ideal_turbine_rpm)
            else:
                pump_load = self.converter.pump_load_torque_nm(self.engine.omega)
                self.engine.step_unlocked(dt, pump_load)
                turbine_torque = self.converter.turbine_torque_nm(pump_load)
                slip_heat_w = abs(pump_load * self.engine.omega - turbine_torque * real_turbine_omega)

            # 3. Gear + final drive multiply turbine torque up to the driveshaft.
            driveshaft_torque = self.transmission.output_torque_nm(turbine_torque)

        # 4. Haldex AWD splits driveshaft torque front/rear: reactively on
        #    last tick's propshaft slip, and proactively on throttle/speed
        #    (real Gen 3+ Haldex pre-tensions the clutch ahead of slip).
        front_drive_torque, rear_drive_torque = self.awd.split(
            driveshaft_torque, self._front_diff_carrier_omega(), self._rear_diff_carrier_omega(),
            self.engine.throttle, self.body.speed_mps,
        )

        # Propshaft: steps from the commanded rear-axle torque, then hands
        # back its own lagged/twisted delivered_torque_nm() -- the shaft's
        # real torsional compliance smoothing/delaying delivery during a
        # transient (launch, gearshift), settling to the commanded torque
        # exactly at steady state. See propshaft.py.
        self.propshaft.step(dt, rear_drive_torque)
        rear_drive_torque = self.propshaft.delivered_torque_nm()

        # 5. Open differentials split each axle's torque left/right — equal
        #    torque regardless of speed, so one wheel can spin freely while
        #    its partner (with more grip) gets no more drive force than it.
        fl_drive, fr_drive = self.front_diff.split(front_drive_torque)
        rl_drive, rr_drive = self.rear_diff.split(rear_drive_torque)

        # CV joints (front half-shafts only -- driven AND steered): a real,
        # if small, efficiency loss at operating (steering) angle + wear.
        left_steer_for_cv, right_steer_for_cv = self.steering.left_right_wheel_angles_rad()
        fl_drive *= self.cv_joints["fl"].efficiency(left_steer_for_cv)
        fr_drive *= self.cv_joints["fr"].efficiency(right_steer_for_cv)

        # Transmission fluid: heated by the real torque-converter slip
        # loss computed above (0.0 when locked -- no slip, no heat).
        self.transmission_fluid.step(
            dt, slip_heat_w, self.outside_temp_c,
            self.transmission_cooler.dissipation_w_per_k(self.body.speed_mps),
        )

        # 6. Friction brakes: front/rear proportioned, split evenly left/right
        #    (real hydraulic brake lines apply equal pressure per side), plus
        #    ESC's single-wheel corrective braking (additive — unlike ABS,
        #    ESC can brake a wheel the driver never asked to brake at all),
        #    then ABS releases/reapplies per wheel to prevent lockup on the
        #    combined total. All using last tick's CAN broadcast — same
        #    explicit-lag pattern as everything else here.
        front_brake_torque, rear_brake_torque = self.brakes.axle_torques_nm(
            self.body.speed_mps, dt, self.brake_booster.assist_fraction(self.vacuum_pump.reservoir_vacuum_kpa)
        )
        fl_brake = fr_brake = front_brake_torque / 2.0
        rl_brake = rr_brake = rear_brake_torque / 2.0

        esc_corrections = self.esc.corrective_brake_torques_nm()
        if esc_corrections:
            brake_sign = 1.0 if self.body.speed_mps > 0 else -1.0
            corner_torques = {"fl": fl_brake, "fr": fr_brake, "rl": rl_brake, "rr": rr_brake}
            for corner, extra_torque_nm in esc_corrections.items():
                corner_torques[corner] -= brake_sign * extra_torque_nm
            fl_brake, fr_brake, rl_brake, rr_brake = (
                corner_torques["fl"], corner_torques["fr"], corner_torques["rl"], corner_torques["rr"],
            )

        fl_brake *= self.abs.brake_multiplier("fl")
        fr_brake *= self.abs.brake_multiplier("fr")
        rl_brake *= self.abs.brake_multiplier("rl")
        rr_brake *= self.abs.brake_multiplier("rr")

        # 7. Suspension load transfer (3-DOF heave/pitch/roll), using last
        #    tick's body accel — same explicit-lag approach as above. Now
        #    genuinely per-corner (not aggregated to front/rear axle totals).
        fl_load, fr_load, rl_load, rr_load = self.ride.step(
            dt, self.body.mass_kg, self.body.ax_mps2, self.body.ay_mps2
        )

        # 8. Suspension kinematics: camber and (bump-steer) toe from each
        #    corner's own compression — see xc90_sim.suspension.kinematics.
        #    Toe adds to the driver's/Ackermann's steer angle; rear wheels
        #    get pure kinematic toe only (a real passive-rear-steer effect
        #    of Volvo's multi-link "Integral Axle" rear, not driver input).
        fl_camber = kinematics.camber_rad("fl", self.ride.fl_deflection_m)
        fr_camber = kinematics.camber_rad("fr", self.ride.fr_deflection_m)
        rl_camber = kinematics.camber_rad("rl", self.ride.rl_deflection_m)
        rr_camber = kinematics.camber_rad("rr", self.ride.rr_deflection_m)
        fl_toe = kinematics.toe_rad("fl", self.ride.fl_deflection_m)
        fr_toe = kinematics.toe_rad("fr", self.ride.fr_deflection_m)
        rl_toe = kinematics.toe_rad("rl", self.ride.rl_deflection_m)
        rr_toe = kinematics.toe_rad("rr", self.ride.rr_deflection_m)

        # 9. Per-wheel kinematics: each of the 4 contact patches has its own
        #    velocity, from rigid-body motion (v_point = v_cg + yaw_rate x r).
        #    Steer angle differs left/right too (Ackermann).
        left_steer, right_steer = self.steering.left_right_wheel_angles_rad()
        half_tf = suspension_specs.FRONT_TRACK_M / 2.0
        half_tr = suspension_specs.REAR_TRACK_M / 2.0
        r = self.body.yaw_rate_rad_s
        vy_front = self.body.vy_mps + suspension_specs.DIST_CG_TO_FRONT_M * r
        vy_rear = self.body.vy_mps - suspension_specs.DIST_CG_TO_REAR_M * r

        fx_fl, fy_fl = self.wheels["fl"].step(
            dt, fl_drive, fl_brake, self.body.vx_mps - half_tf * r, vy_front,
            left_steer + fl_toe, fl_load, fl_camber,
        )
        fx_fr, fy_fr = self.wheels["fr"].step(
            dt, fr_drive, fr_brake, self.body.vx_mps + half_tf * r, vy_front,
            right_steer + fr_toe, fr_load, fr_camber,
        )
        fx_rl, fy_rl = self.wheels["rl"].step(
            dt, rl_drive, rl_brake, self.body.vx_mps - half_tr * r, vy_rear, rl_toe, rl_load, rl_camber
        )
        fx_rr, fy_rr = self.wheels["rr"].step(
            dt, rr_drive, rr_brake, self.body.vx_mps + half_tr * r, vy_rear, rr_toe, rr_load, rr_camber
        )

        # 10. Vehicle body: 3-DOF planar dynamics (longitudinal, lateral, yaw) + world pose.
        self.body.step(dt, {
            "fl": (fx_fl, fy_fl), "fr": (fx_fr, fy_fr), "rl": (fx_rl, fy_rl), "rr": (fx_rr, fy_rr),
        })

        # 10.5. Airbags/SRS: crash sensing off the real body-frame accel just
        # computed above — see xc90_sim.cabin.AirbagSystem. This sim has no
        # collision physics, so under normal driving these accel values never
        # reach deployment thresholds; the wiring is real, a crash scenario
        # just isn't simulated.
        self.airbag_system.step(dt, self.body.ax_mps2, self.body.ay_mps2, self.ignition.accessory_power)

        # GPS: real lat/lon fix from the body's own real local position —
        # see xc90_sim.cabin.GPS.
        self.gps.step(self.body.world_x_m, self.body.world_y_m, self.body.heading_rad)

        # 11. Body control module: power tailgate actuation timer, speed-based
        #     auto-lock — see xc90_sim.body. Not vehicle-dynamics physics, but
        #     still needs a tick to advance its own timers/state.
        self.closures.step(dt, self.body.speed_mps)
        self.windows.step(dt)
        self.lighting.step(dt)
        self.wipers.step(dt)
        self.sunroof.step(dt)
        # Dome light: real door-open state OR the driver's manual override —
        # composed here rather than coupling Lighting itself to Closures.
        self.lighting.dome_light_on = self.closures.any_door_open() or self.lighting.dome_light_override

        # Oil life monitor: counts down real miles driven since the last
        # reset. body.distance_m is already a proper odometer (accumulated
        # via hypot, so it's correct regardless of direction — see
        # VehicleBody.step()); track its delta rather than differentiating
        # speed, so this can't drift out of sync with the real odometer.
        distance_delta_m = self.body.distance_m - self._last_distance_m
        self.oil_life_monitor.add_miles(distance_delta_m / 1609.344)
        self._last_distance_m = self.body.distance_m

        # Fuel tank: drawn down by real fuel mass burned this tick (the
        # engine's cylinders track cumulative fuel injected — see
        # Engine.total_fuel_burned_kg), the same delta-tracking pattern as
        # the odometer/oil-life above rather than an estimated MPG figure.
        fuel_burned_delta_kg = self.engine.total_fuel_burned_kg - self._last_fuel_burned_kg
        self.fuel_tank.consume_kg(fuel_burned_delta_kg)
        self._last_fuel_burned_kg = self.engine.total_fuel_burned_kg

        # Cooling system: coolant temperature evolves from real fuel energy
        # input (the delta just computed above) minus radiator rejection —
        # see xc90_sim.cooling.CoolingSystem. Water pump steps first so this
        # tick's radiator rejection reflects this tick's real coolant flow.
        high_load = self.engine.throttle > 0.6
        self.water_pump.step(dt, self.cooling_system.coolant_temp_c, self.ignition.engine_running, high_load)
        fuel_energy_rate_w = (fuel_burned_delta_kg * cylinder_specs.FUEL_LHV_J_PER_KG) / dt if dt > 0 else 0.0
        self.cooling_system.step(
            dt, fuel_energy_rate_w, self.body.speed_mps, self.outside_temp_c, self.water_pump.flow_frac
        )

        # 11.5. HVAC: cabin temperature evolves each tick from ambient heat
        #       exchange + HVAC output — see xc90_sim.cabin.HVAC. No solar
        #       load modeled (would need real sun angle/position, not built).
        #       Heating (not cooling) is gated by real coolant temperature —
        #       a cold engine can't provide much cabin heat yet.
        self.hvac.step(dt, self.outside_temp_c, heating_available_frac=self.cooling_system.heating_available_frac())

        # 11.6. Park Assist Pilot: gap-scan bookkeeping while scanning, or
        # phase-completion/safety-abort checks while actively maneuvering.
        self.park_assist_pilot.step(
            self.body.distance_m, self.body.heading_rad,
            self.parking_assist.front_distance_m, self.parking_assist.rear_distance_m,
        )

        # 12. ECUs broadcast the tick's state onto the CAN bus (own schedules; see xc90_sim.ecu).
        for ecu in self.ecus:
            ecu.step(dt)

        self.time_s += dt

    def telemetry(self):
        return {
            "time_s": self.time_s,
            "speed_mph": self.body.speed_mps * 2.23694,
            "distance_m": self.body.distance_m,
            "world_x_m": self.body.world_x_m,
            "world_y_m": self.body.world_y_m,
            "heading_deg": math.degrees(self.body.heading_rad),
            "engine_rpm": self.engine.rpm,
            "gear": self.transmission.gear,
            "converter_locked": self.converter.locked,
            "accel_g": self.body.ax_mps2 / 9.80665,
            "lateral_accel_g": self.body.ay_mps2 / 9.80665,
            "steering_wheel_deg": self.steering.wheel_angle_deg,
            "yaw_rate_deg_s": math.degrees(self.body.yaw_rate_rad_s),
            "sideslip_deg": math.degrees(math.atan2(self.body.vy_mps, max(self.body.vx_mps, 0.1))),
            "pitch_deg": math.degrees(self.ride.theta),
            "roll_deg": math.degrees(self.ride.phi),
            "doors_locked": self.closures.locked,
            "any_door_open": self.closures.any_door_open(),
            "hood_open": self.closures.hood_open,
            "tailgate_open": self.closures.tailgate_open,
            "ajar_warning": self.closures.ajar_warning(),
            "cabin_temp_c": self.hvac.cabin_temp_c,
            "cruise_engaged": self.steering_wheel_controls.cruise_control_engaged,
            "cruise_set_speed_kph": self.steering_wheel_controls.cruise_set_speed_kph,
            "acc_lead_vehicle_detected": self.forward_radar.target_detected(),
            "acc_follow_gap_setting": self.adaptive_cruise.follow_gap_setting,
            "lka_enabled": self.lane_keeping_assist.enabled,
            "lka_lane_detected": self.lane_camera.lane_detected,
            "front_park_zone": self.parking_assist.front_zone(),
            "rear_park_zone": self.parking_assist.rear_zone(),
            "active_park_zone": self.active_park_zone(),
            "unbelted_occupied_seats": self.seating.unbelted_occupied_seats(),
            "airbags_deployed": [name for name, bag in self.airbag_system.airbags.items() if bag.deployed],
            "srs_warning_light": self.airbag_system.warning_light_on(),
            "gear_selector": self.gear_selector.position,
            "window_positions_pct": dict(self.windows.position_pct),
            "mirrors_folded": self.mirrors.folded,
            "headlight_mode": self.lighting.headlight_mode,
            "drl_on": self.lighting.drl_on(self.ignition.engine_running),
            "left_indicator_lit": self.lighting.left_indicator_lit(),
            "right_indicator_lit": self.lighting.right_indicator_lit(),
            "left_blind_spot_warning": self.blind_spot_monitor.left_warning(self.body.speed_mps),
            "right_blind_spot_warning": self.blind_spot_monitor.right_warning(self.body.speed_mps),
            "ignition_state": self.ignition.state,
            "engine_running": self.ignition.engine_running,
            "park_pilot_phase": self.park_assist_pilot.phase,
            "park_pilot_gap_length_m": self.park_assist_pilot.found_gap_length_m,
            "engine_auto_stopped": self.auto_stop_start.engine_auto_stopped,
            "front_wiper_speed": self.wipers.front_speed,
            "rear_wiper_speed": self.wipers.rear_speed,
            "sunroof_glass_state": self.sunroof.glass_state,
            "sunroof_shade_open": self.sunroof.shade_open,
            "available_cargo_volume_l": self.storage.available_cargo_volume_l(self.seating),
            "tire_pressures_psi": dict(self.tpms.pressures_psi),
            "tire_pressure_warning": self.tpms.any_warning(),
            "oil_life_pct": round(self.oil_life_monitor.life_pct(), 1),
            "oil_change_due": self.oil_life_monitor.change_due(),
            "infotainment_screen": self.infotainment.current_screen,
            "gps_lat": self.gps.lat,
            "gps_lon": self.gps.lon,
            "gps_heading_deg": self.gps.heading_deg,
            "gps_has_fix": self.gps.has_fix(),
            "fuel_level_l": round(self.fuel_tank.level_l, 2),
            "fuel_level_frac": round(self.fuel_tank.level_fraction(), 3),
            "low_fuel_warning": self.fuel_tank.low_fuel_warning(),
            "fuel_ethanol_pct": round(self.fuel_tank.ethanol_fraction * 100.0, 1),
            "fuel_octane_aki": round(self.fuel_tank.octane_aki, 1),
            "fuel_days_since_fill": round(self.fuel_tank.days_since_fill, 1),
            "fuel_octane_boost_derate_pct": round(self.fuel_tank.octane_boost_derate_frac() * 100.0, 1),
            "fuel_staleness_derate_pct": round(self.fuel_tank.staleness_combustion_derate_frac() * 100.0, 1),
            "manifold_pressure_bar": round(self.engine.manifold_pressure_pa / 1e5, 3),
            "timing_belt_service_due": self.wear.service_due("timing_belt"),
            "accessory_belt_service_due": self.wear.service_due("accessory_belt"),
            "engine_mounts_service_due": self.wear.service_due("engine_mounts"),
            "battery_12v_condition_pct": round(self.wear.age_condition("battery_12v") * 100.0, 1),
            "battery_12v_service_due": self.wear.age_service_due("battery_12v"),
            "camshaft_angle_deg": round(self.engine.camshaft_angle_deg, 1),
            "fuel_rail_pressure_bar": round(self.engine.fuel_pump.pressure_bar, 1),
            "injector_pulse_width_ms": round(self.engine.cylinders[0].fuel_injector.last_pulse_width_ms, 2),
            "electrical_demand_w": round(self.engine.electrical_demand_w, 1),
            "ac_compressor_active": self.engine.ac_compressor_active,
            "battery_charge_pct": round(self.battery.charge_frac * 100.0, 1),
            "battery_low_charge_warning": self.battery.low_charge_warning(),
            "support_battery_charge_pct": round(self.support_battery.charge_frac * 100.0, 1),
            "vacuum_reservoir_kpa": round(self.vacuum_pump.reservoir_vacuum_kpa, 1),
            "vacuum_pump_running": self.vacuum_pump.running,
            "brake_booster_assist_pct": round(
                self.brake_booster.assist_fraction(self.vacuum_pump.reservoir_vacuum_kpa) * 100.0, 1
            ),
            "pcv_blowby_flow_pct": round(self.engine.pcv_valve.blowby_flow_fraction * 100.0, 3),
            "blown_fuses": [name for name, f in self.fuse_box.fuses.items() if f.blown],
            "pulled_fuses": [name for name, f in self.fuse_box.fuses.items() if f.pulled],
            "engine_removed": self.engine_removed,
            "battery_disconnected": self.battery.disconnected,
            "relay_faults": [
                name for name, relay in self.relay_box.relays.items()
                if relay.stuck_open or relay.stuck_closed
            ],
            "brake_lights_on": self.lighting.brake_lights_on,
            "reverse_lights_on": self.lighting.reverse_lights_on,
            "fog_lights_on": self.lighting.fog_lights_on,
            "dome_light_on": self.lighting.dome_light_on,
            "horn_honking": self.horn.honking,
            "washer_fluid_l": round(self.washer_fluid.level_l, 3),
            "washer_fluid_low_warning": self.washer_fluid.low_warning(),
            "coolant_temp_c": round(self.cooling_system.coolant_temp_c, 1),
            "thermostat_open": self.cooling_system.thermostat_open,
            "cooling_fan_on": self.cooling_system.fan_on,
            "water_pump_flow_pct": round(self.water_pump.flow_frac * 100.0, 1),
            "water_pump_failed": self.water_pump.failed,
            "engine_overheating": self.cooling_system.overheating(),
            "catalyst_temp_c": round(self.engine.exhaust_system.catalyst_temp_c, 1),
            "catalyst_active": self.engine.exhaust_system.catalyst_active(),
            "o2_sensor_lambda": round(self.engine.oxygen_sensors[0].lambda_reading, 3),
            "egr_flow_fraction": round(self.engine.egr_valve.flow_fraction, 3),
            "turbo_boost_bar": round(self.engine.turbocharger.boost_pa / 1e5, 3),
            "transmission_fluid_temp_c": round(self.transmission_fluid.temp_c, 1),
            "transmission_fluid_overheating": self.transmission_fluid.overheating(),
            "propshaft_windup_deg": round(np.degrees(self.propshaft.windup_angle_rad), 3),
            "wheel_bearings_service_due": self.wear.service_due("wheel_bearings"),
            "cv_joints_service_due": self.wear.service_due("cv_joints"),
            "transmission_fluid_service_due": self.wear.service_due("transmission_fluid"),
        }
