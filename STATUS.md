# 2016 Volvo XC90 T6 AWD — Python Simulation: Current State

Goal: simulate the real 2016 XC90 T6 AWD (Drive-E twincharged I4, Aisin
TG-81SC 8-speed, Haldex AWD) component-by-component, using publicly
documented specs wherever they exist, and clearly flagged assumptions where
they don't. See `GLOSSARY.md` for plain-English explanations of every
technical term used across the codebase.

**This models a specific real car**: VIN `YV4A22PKXG1092057`, T6 Momentum
(not Inscription — corrected after the owner's CARFAX confirmed trim), AWD,
115,367 mi as of 2026-01-28. Identity metadata lives in
`specs/vehicle_identity.py`; the car's real service history (turbo replaced
at 10,135 mi, several brake jobs, tires last replaced at 59,860 mi, etc.)
lives in `specs/service_history.py` and actually degrades physics via
`wear/wear_model.py` — see "What's implemented" below. Real spec corrections
from this research: curb mass is 1,935 kg (published T6 AWD Momentum
weight, not the 2,100 kg Inscription-trim guess used earlier); tire size is
235/55R19 (the owner's confirmed actual wheel, `TIRE_ROLLING_RADIUS_M =
0.3706`); front/rear weight distribution is 52/48 (published, not the 55/45
guess used earlier). All three ripple through the whole vehicle model
(spring rates, effective gearing, traction, roll dynamics) — see "What's
implemented" and "Known tuning gaps" for how 0-60 moved as each was applied.

## Architecture

Every subsystem is an independent class with a small `step()` interface, so
pieces can be replaced without touching the rest (e.g. swap the engine for an
EV motor, or the Haldex clutch for a locked center diff).

```
xc90_sim/
  specs/            spec constants, one module per subsystem
    engine.py         Drive-E 2.0L twincharged I4 (torque curve, redline, boost lag)
    transmission.py   TG-81SC 8-speed ratios, torque converter capacity/ratio curves
    awd.py            Haldex front/rear torque-split behavior
    chassis.py        mass, aero, tire friction, brake proportioning
    suspension.py     spring/damper rates (derived from ride-frequency targets),
                       CG height/weight split, roll stiffness, pitch/roll inertia
    steering.py       steering ratio (derived from published turning circle + wheelbase)
    tire.py           Magic-Formula-style shape factors, slip relaxation lengths
    service_history.py real CARFAX-derived service events for this specific car —
                       edit this to reflect a new real repair (see wear/, below)

  engine/
    engine.py         Drive-E 2.0L twincharged I4: crank rotational dynamics driven by 4
                       real Cylinders (below) -- real twincharger boost model (instant
                       supercharger + laggy turbo), fuel injection, accessory load, plus
                       step_off/step_cranking for ignition-off/starter behavior
    cylinder.py       Cylinder: real single-zone combustion thermodynamics (slider-crank
                       geometry, Wiebe heat-release ODE) for one cylinder; owns a Camshaft
                       + FuelInjector
    camshaft.py       Camshaft: owns real Valve objects (2 intake + 2 exhaust per
                       cylinder), delegates open/closed + lift to them
    valve.py          Valve: real raised-cosine lift curve vs. crank angle
    flywheel.py       Flywheel: inertia DERIVED from mass/radius, not a bare constant
    timing_belt.py    TimingBelt: real 2:1 cam:crank ratio, wear-linked retard

  fuel_system/
    fuel_tank.py      FuelTank: real level/capacity, drawn down by actual fuel burned
    fuel_pump.py      FuelPump: electric lift pump + HP pump, real pressure build/bleed
    fuel_injector.py  FuelInjector: commanded fuel mass -> real pulse width (ms), derated
                       by low rail pressure

  electrical/
    alternator.py      Alternator: real electrical demand -> genuine crank-torque draw
    battery.py         Battery: 12V AGM, charges/discharges for real, gates start_engine()
    accessory_belt.py  AccessoryBelt: drives the alternator/AC compressor (this car has
                       ELECTRIC power steering -- no belt-driven steering pump)
    auto_stop_start.py AutoStopStart: engine-off-at-a-stop fuel saving, engine only --
                       distinct from Ignition, which stays RUN throughout

  exhaust/
    exhaust_system.py ExhaustSystem: catalytic converter light-off thermal lag, real
                       exhaust backpressure fed back into the cylinder's exhaust-stroke
                       pumping loss
    oxygen_sensor.py  OxygenSensor: reads real per-cylinder AFR -> lambda, with response
                       lag + measurement noise (one per cylinder)
    egr_valve.py      EGRValve: models EGR as a reduction in effective trapped fresh
                       charge, ramped by rpm/load band
    turbocharger.py   Turbocharger: exhaust-driven boost lag (the laggy half of the
                       twincharger; supercharger half stays on Engine/AccessoryBelt)

  cooling/
    cooling_system.py CoolingSystem: coolant temp from real fuel-energy heat in vs.
                       thermostat-gated radiator + ambient rejection; feeds HVAC's
                       heating_available_frac

  transmission/
    transmission.py       Transmission: gear ratios, adaptive auto-shift map, Geartronic
                          manual mode
    torque_converter.py   TorqueConverter: capacity-factor pump load + torque-ratio
                          multiplication + lockup
    gear_selector.py      GearSelector: P/R/N/D, user-only, brake-shift + speed interlocks
    transmission_fluid.py TransmissionFluid: temp driven by real torque-converter slip-
                          loss heat, cooled by a real cooler term

  drivetrain/
    differential.py   OpenDifferential: equal L/R torque split, independent speeds
    drivetrain.py     Haldex AWD front/rear torque split based on propshaft slip
    propshaft.py      Propshaft: real torsional windup from rear-axle torque, closed
                       back into the torque path via delivered_torque_nm()
    cv_joint.py       CVJoint: front half-shaft efficiency loss vs. steer angle + wear
                       (bounded, small)
    wheel_bearing.py  WheelBearing: per-corner rolling-resistance scale from wear
                       (bounded, small)

  chassis/
    tire_model.py     nonlinear saturating tire (nonlinear Magic-Formula curves +
                       friction-ellipse combined slip)
    wheel.py          Wheel: one wheel's slip ratio/angle -> tire forces -> rotational
                       dynamics (4 instances: FL/FR/RL/RR, not axle-lumped)
    brakes.py         pedal -> front/rear brake torque (split evenly L/R, routed through
                       the same traction-limited per-wheel model as drive torque)
    vehicle_body.py   3-DOF planar rigid body (vx, vy, yaw rate) + world x/y/heading;
                       yaw moment is the true sum of each wheel's r x F about the CG

  suspension/
    corner.py         single spring+damper force law (stateless)
    ride_model.py     3-DOF rigid sprung mass (heave/pitch/roll) on 4 corners,
                       Newton-Euler dynamics + anti-roll bars, real inertia/damping
                       (not quasi-static); returns genuine per-corner normal loads
                       and per-corner deflection (for kinematics, below)
    kinematics.py     camber/toe vs. corner compression; camber now comes from
                       linkage_geometry.py (below), toe stays a flat gain
    linkage_geometry.py real 3D hardpoint kinematics: instant-center/swing-arm
                       method (front double-wishbone, rear multi-link) derives
                       camber gain, roll center height, anti-dive/anti-squat
                       from actual control-arm coordinates (specs/linkage.py),
                       not an assumed flat curve

  steering/
    geometry.py       steering wheel angle -> Ackermann-corrected wheel angles

  sim/
    simulation.py     orchestrates the tick: engine -> converter -> transmission ->
                       Haldex -> axles (tire model) -> body (3-DOF + world pose) ->
                       ECUs (CAN broadcast). Owns no physics itself, only sequencing.

  network/
    can_message.py    CANSignal/CANMessage: byte-packed encode/decode (scale+offset)
    can_bus.py        CANBus: in-process publish/subscribe by arbitration ID

  ecu/                observational layer — reads live sim state, broadcasts it on a
                       schedule, same as a real vehicle network. Doesn't feed physics.
    base.py           ECU base: generic periodic-message scheduling
    engine_ecu.py     0x0C0 ENGINE_DATA (100 Hz): rpm, throttle%, calculated load%
    transmission_ecu.py 0x0D0 TRANS_DATA (50 Hz): gear, converter lock, mode, input rpm
    chassis_ecu.py    0x0E0/1/2/3: wheel speeds (via wheel_speed_sensor.py — quantized +
                       noisy, not exact omega), lateral/long accel, yaw rate, steering,
                       brake pedal%, vehicle reference speed (median-of-4-wheels
                       "select" estimate, not ground truth — for dsc/, below)
    wheel_speed_sensor.py reluctor-ring pulse quantization + measurement noise;
                       imprecise at low speed, same as real sensors
    awd_ecu.py        0x0F0 AWD_DATA (20 Hz): Haldex front/rear torque bias
    body_ecu.py       0x1A0-4: doors/hood/tailgate/lock, windows, lighting,
                       wipers, sunroof (see body/, below)
    cabin_ecu.py      0x1B0-6: HVAC, park-assist distances, infotainment,
                       seatbelt-reminder, BLIS, TPMS, oil life (see cabin/, below)

  body/               body control module domain — discrete state/timers, not
                       vehicle-dynamics physics
    closures.py       Closures: 4 doors, hood, power tailgate (timed open/
                       close cycle, not instant), central locking (blocked
                       while any door's open, driver-only unlock option),
                       speed-based auto-lock
    windows.py        Windows: rate-based power windows, one-touch up/down
    mirrors.py        Mirrors: fold/unfold (auto-tied to central locking), heated
    lighting.py       Lighting: headlight modes, turn indicators with real
                       blink timing, hazards, DRLs gated on engine running
    ignition.py       Ignition: rotary Start/Stop knob, OFF/ACCESSORY/
                       cranking/RUN, brake-to-start interlock
    wipers.py         Wipers: front/rear speeds with a real sweep-cycle timer
    sunroof.py        Sunroof: glass panel + independent shade, with the real
                       shade-must-open-before-glass mechanical interlock
    horn.py           Horn: simple momentary circuit
    washer_fluid.py   WasherFluid: real small consumable, depleted by spray events

  cabin/              cabin electronics domain — discrete state/timers plus
                       one genuine physical model (HVAC thermal), not
                       vehicle-dynamics physics (cruise control and Park
                       Assist Pilot are the exceptions: both feed back into
                       throttle/brake/steering — see sim/simulation.py step())
    hvac.py           HVAC: real first-order thermal model — cabin temp
                       evolves from ambient heat exchange + HVAC output
                       (heating/cooling capacity scaled by fan speed), not
                       just a setpoint display
    parking_assist.py ParkingAssist: front/rear obstacle distance -> warning
                       zone -> tone interval; connects to the engine/brakes
                       via Simulation's low-speed collision mitigation
    park_assist_pilot.py ParkAssistPilot: genuine semi-autonomous parallel
                       parking -- gap-scan, then a real steering-angle
                       takeover through a two-phase geometric maneuver
    blind_spot_monitor.py BlindSpotMonitor: BLIS, speed-gated
    infotainment.py   Infotainment: power/volume/source/mute, touchscreen
                       menu screens (home/media/nav/climate/park_assist/
                       seats/car_status), + a navigation status pass-through
                       (destination/distance/ETA)
    seats.py          Seat/Seating: occupancy, seatbelt buckle state (drives
                       the seatbelt reminder), heating (front-only per this
                       trim), power position, fold-flat (2nd/3rd row only),
                       across the real 2-3-2 layout
    storage.py        Storage: glove box / center console open-closed state,
                       cargo volume connected to Seating's actual fold state
    controls.py       SteeringWheelControls + CruiseController (closed-loop
                       proportional speed tracking, cancels on brake press)
                       + PedalInputs (0-100% -> physical travel mm)
    tpms.py           TPMS: per-wheel pressure vs. recommended, warns at the
                       real FMVSS 138 25%-low federal threshold
    maintenance.py    OilLifeMonitor: miles-since-reset countdown (not a
                       literal oil-quality sensor), reset via a service menu

  dsc/                Dynamic Stability & Traction Control (Volvo's DSTC) — actual
                       intervention, not just observation. Senses over the CAN bus
                       like a real module would; actuates via a direct call.
    traction_control.py cuts engine torque when a driven wheel's slip exceeds
                       threshold during acceleration
    abs.py            releases/reapplies per-wheel brake torque to prevent lockup
    esc.py            compares actual yaw rate to a kinematic reference and brakes
                       one wheel (inside-rear for understeer, outside-front for
                       oversteer) — can brake a wheel the driver never touched

  trip/               point-A-to-B trip tooling
    drive_cycle.py    synthetic speed-vs-time profile from (distance, style) —
                       fallback when live routing isn't used/available
    live_routing.py   real routing: Nominatim (geocode) + OSRM (real turn-by-
                       turn route) + Overpass (real traffic signal/stop-sign
                       locations) -> a drive cycle built from the actual road,
                       not a style guess. No API key needed for any of the three.
    driver_model.py   rate-limited proportional throttle/brake controller
    logger.py         CAN-bus datalogger: time-weighted usage stats per component
    runner.py         shared "run this DriveCycle through a Simulation" loop

  wear/               mileage-based wear/degradation model — makes the sim
                       reflect THIS car's actual current condition, not a
                       showroom-new one
    wear_model.py     generic WearModel: condition fraction per component from
                       "miles since its last service_history replacement event"

  obd/                bridges a REAL car's OBD2 port onto the same CANBus/message
                       formats the simulated ECUs use, so TripLogger works
                       unchanged on real data. UNTESTED against real hardware
                       (written against python-OBD's documented API; no adapter
                       or car was available to verify against) — see its module
                       docstrings for exactly what generic OBD2 can and can't
                       provide, and examples/run_obd_trip.py for troubleshooting.
    connection.py     thin wrapper over python-OBD; USB or WiFi via the same
                       portstr (pyserial's socket:// URL scheme covers WiFi)
    bridge.py         polls RPM/speed/throttle/load; derives gear (matched
                       against this project's own real TG-81SC ratios) and
                       longitudinal accel (speed derivative, clamped to a
                       physically sane range); publishes onto the CAN bus

examples/
  zero_to_sixty.py    validation script (full-throttle standing-start run)
  run_trip.py         run a synthetic (distance, style) trip, print usage report
  run_real_trip.py    run a REAL trip between two addresses, print usage report
  run_obd_trip.py     log a REAL trip from your actual car's OBD2 port
```

## What's implemented

- **Engine**: real torque curve (400 Nm plateau 2200-5400 rpm, 316 hp @ 5700
  rpm, matches published spec), crank inertia, friction, boost-response lag
  (twincharger design largely eliminates classic turbo lag).
- **Torque converter**: proper two-curve model (capacity factor for pump
  absorption, torque ratio for multiplication) + lockup clutch. The lockup
  *decision* and the *fluid-coupling physics* deliberately use two different
  turbine-speed signals — see "Bugs found and fixed" below.
- **Transmission**: real TG-81SC gear ratios, adaptive auto-shift map, plus a
  Geartronic **manual tip-shift mode** (`set_transmission_mode('manual')`,
  `request_upshift()/request_downshift()`) with over-rev/stall protection
  active in both modes.
- **Haldex AWD**: front-biased under low slip, shifts toward 50/50 under
  detected propshaft slip (front vs. rear differential carrier speed).
- **Per-wheel modeling**: 4 independent `Wheel` objects (not 2 lumped axles),
  each with its own tire slip state, normal load, and torque. Front and rear
  each get an `OpenDifferential` (equal torque split, independent speeds) —
  a wheel can genuinely spin while its partner doesn't. Per-wheel kinematics
  (`v_point = v_cg + yaw_rate x r`) give the outer wheels a real speed
  advantage in a turn, and Ackermann steering angles differ left/right.
  Confirmed working: outer wheels spin faster in a steady turn, and an
  isolated left/right drive-force imbalance produces genuine torque-steer
  yaw in the correct direction.
- **Tire model**: nonlinear, saturating (real grip peak ~15-20% slip ratio /
  ~8-10° slip angle, mild falloff beyond), combined via a friction ellipse —
  not a flat Coulomb cap.
- **Suspension**: genuine 3-DOF (heave/pitch/roll) rigid-body dynamics on 4
  independent corner springs/dampers, with bump/droop stops and anti-roll
  bars now actually wired into the roll equation (see bug #8 below). Squat/
  dive/roll have real inertia and settle to physically sensible values
  (~0.8° squat at 3 m/s², ~4.9° roll at 0.8g).
- **Kinematic suspension linkage**: camber, roll center height, and anti-
  dive/anti-squat are now derived from actual 3D control-arm hardpoints
  (`specs/linkage.py`) via the instant-center/swing-arm method — the
  standard hand-calculation technique from vehicle dynamics texts (Milliken
  & Milliken), not an assumed flat curve. No real Volvo hardpoints are
  published, so the coordinates are ASSUMPTION, but they were *solved for*
  (not guessed) to land the resulting geometry in plausible real-world
  ranges: front roll center 101mm / rear 150mm above ground (typical
  crossover range 60-200mm), front camber gain ~2.9° / rear ~1.4° over 80mm
  of travel (typical double-wishbone/multi-link full-travel range 2-4°),
  front anti-dive 15% / rear anti-squat 16% (typical range 10-30%). The
  roll-center height now correctly reduces the roll moment arm (CG height
  *above the roll axis*, not above the ground — 497mm effective arm vs.
  620mm raw CG height, ~20% less), and anti-dive/anti-squat measurably
  reduce pitch during braking/acceleration (dive dropped from ~2.2° to
  ~1.5-1.6° during sustained hard braking). Toe remains a flat linear gain
  (a dedicated toe-link isn't captured by this same swing-arm model); it
  still feeds directly into each wheel's effective steer angle, including
  the REAR wheels, which get genuine passive bump-steer with no driver
  input — exactly what a multi-link rear axle is designed to produce.
- **Steering**: Ackermann geometry (individual left/right wheel angles, not
  just an average); steering ratio back-derived from Volvo's published
  12.1 m turning circle + 2.8 turns lock-to-lock (a calculation from two
  real numbers, not a free guess).
- **Vehicle body**: unified 3-DOF planar rigid body (longitudinal, lateral,
  yaw) with world-frame x/y/heading integration — a steering input traces an
  actual, plottable path. Yaw moment is now the true sum of all 4 wheels'
  `r x F` about the CG, not an axle-level approximation.
- **Brakes**: front/rear proportioned, split evenly left/right, routed
  through the same traction-limited per-wheel model as drive torque (so
  hard braking can lock a wheel, same physics either way).
- **Body control module (doors, hood, power tailgate, central locking)**:
  `xc90_sim/body/Closures` tracks each door's open/closed state, the hood,
  and the power tailgate (a real, standard-on-Momentum feature) as a timed
  open/close cycle (`TAILGATE_ACTUATION_TIME_S`), not an instant flip.
  Central locking can't engage with a door standing open (mirrors real BCM
  behavior); a speed-based auto-lock engages once above
  `AUTO_LOCK_SPEED_MPS` with every door shut, same as the real car's "Auto
  door lock" feature. Broadcast on the CAN bus via `BodyECU` (0x1A0
  BODY_STATUS, 10 Hz), including a real BCM-style `ajar_warning` (any
  closure not fully shut). `Simulation` exposes `set_door()`, `set_hood()`,
  `request_tailgate()`, `lock_doors()`/`unlock_doors()`. Doesn't feed back
  into vehicle-dynamics physics — this is the first of the "vehicle
  software features" bucket (see "Left to do") to get built.
- **Cabin electronics (HVAC, parking sensors, infotainment, seats, storage,
  steering wheel buttons + cruise control, pedal travel)**: the second
  chunk of that same "vehicle software features" bucket. `xc90_sim/cabin/`:
  - `HVAC` is a genuine first-order thermal model (not a setpoint display)
    — cabin temp evolves from ambient heat exchange + HVAC output each
    tick, tuned to warm up over a few real minutes at full fan, same order
    of magnitude as an actual car. No solar load (sun angle/position isn't
    modeled).
  - `ParkingAssist` takes a front/rear obstacle distance and returns a
    warning zone (far/near/critical) and tone interval — sensor/warning
    layer only, no automated self-parking steering (a much bigger robotics
    problem, explicitly out of scope).
  - `Infotainment` tracks power/volume/source/mute plus a navigation
    pass-through (destination/distance/ETA) — deliberately not coupled to
    `trip/live_routing.py` internally, so a caller with a real route
    pushes its own numbers in rather than this reaching into trip/.
  - `Seating` models the real 2-3-2 (7-seat) layout: occupancy + seatbelt
    buckle state per seat drives a genuine **seatbelt reminder**
    (`unbelted_occupied_seats()` — occupied but not buckled); front-seat
    heating only, since rear-seat heating is an ASSUMPTION-flagged
    Inscription-trim option not confirmed fitted to this VIN.
  - `Storage` (glove box / center console open-closed) and published cargo
    volumes (314L behind row 3 / 1,858L max, in `specs/cabin.py`).
  - **Cruise control is the one part of this bucket that feeds back into
    vehicle-dynamics physics**: `CruiseController` (a self-contained
    proportional controller, deliberately NOT reusing
    `trip/driver_model.py`'s — see its docstring — since `trip/` sits
    *above* `sim/` and reaching back down would create a circular import)
    overrides manual throttle/brake in `Simulation.step()` while engaged.
    Like the reused pattern it's based on, it has the well-known
    proportional-control characteristic of steady-state droop under load
    (e.g. settled ~9 kph under a 164 kph set-speed at highway speed in
    testing) rather than perfect tracking — an honest characteristic of
    the technique, not a bug.
  - Broadcast via `CabinECU` (0x1B0-4: HVAC_DATA, PARK_ASSIST_DATA,
    INFOTAINMENT_DATA, SEATBELT_DATA, BLIS_DATA). `Simulation` exposes
    matching setters (`set_hvac_*`, `set_*_park_obstacle_m`, `press_cruise_*`,
    `set_seat_*`, `set_glove_box`/`set_center_console`).
- **PRND gear selector + real reverse driving** (`xc90_sim.transmission.
  GearSelector`): P/R/N/D changes ONLY on an explicit `set_gear_selector()`
  call — nothing in this simulation ever shifts it automatically. Two real
  safety interlocks: a brake-shift interlock (can't leave Park without the
  brake pedal pressed) and a speed interlock (can't select Park/Reverse
  above a walking pace). `Simulation.step()` branches on the selector's
  position: Park/Neutral cuts driveshaft torque to exactly 0 (engine still
  idles/revs against the torque converter's always-coupled pump, same as a
  real car); Reverse uses a single fixed ratio (`REVERSE_RATIO`, defined in
  specs since early in the project but never actually wired in before now)
  instead of the forward 1-8 gear table; Drive is the original, unchanged
  code path. Enabling Reverse required removing two forward-only clamps
  (`vx_mps` and wheel `omega` were both hard-floored at 0) that turned out
  to have been silently masking a real brake-model bug the whole time —
  see bug #13, since fixed. `active_park_zone()` composes the gear
  selector with `ParkingAssist` (rear zone while reversing = "park in",
  front zone in Drive = "park out") without pushing gear-awareness down
  into `ParkingAssist` itself, which stays standalone/testable.
  Cross-wired: cruise control requires Drive and cancels itself on any
  other selection (see below).
- **Cruise control's real interlocks**: requires the gear selector to be
  in Drive to engage at all, and cancels itself if TCS or ABS actively
  intervenes (`TractionControl.is_active()` / `ABS.is_active()`, added for
  this) — same as a real car backing off cruise control when the road
  surface itself signals reduced grip, not just on a manual brake press
  (which already cancelled it).
- **Windows, mirrors, lighting, blind-spot monitor, door-lock refinement,
  head restraints** — the remaining pieces of "vehicle software features":
  - `xc90_sim.body.Windows`: one position (0-100%) per door, moving at a
    constant rate toward a requested target (unlike the power tailgate's
    fixed-duration cycle, a real window motor moves at roughly constant
    speed regardless of travel distance) — one-touch up/down is just
    `request_window(corner, 0)` / `request_window(corner, 100)`.
  - `xc90_sim.body.Mirrors`: fold/unfold + heated state. Cross-wired to
    `Closures`: folds automatically on `lock_doors()`, unfolds on
    `unlock_doors()`/`unlock_driver_door_only()` — a real, common feature,
    not two independent pieces of state that happen to both exist.
  - `xc90_sim.body.Lighting`: headlight mode (off/parking/low/high beam),
    turn indicators with *real* blink timing (`INDICATOR_BLINK_HZ`, not
    just an on/off flag), hazards, and DRLs that auto-on whenever the
    headlights aren't manually switched to low/high beam (this sim has no
    ignition on/off state — `Simulation` existing models the engine as
    always running — so "DRL on while running with headlights off"
    simplifies to just that condition).
  - `xc90_sim.cabin.BlindSpotMonitor` (BLIS — Volvo's real feature/name):
    left/right occupied -> warning, gated by a minimum speed
    (`BLIS_MIN_SPEED_MPS`) so parking-lot proximity doesn't false-positive,
    same as real BLIS.
  - `Closures.unlock_driver_only()`: real single-stage remote-unlock
    behavior (only the driver's door "opens" on first press; a second
    press — `unlock()` — opens the rest), alongside the existing full
    `unlock()`.
  - `Seat.head_restraint_up`: folds down for cargo/visibility, especially
    2nd/3rd row.
  - Broadcast via `BodyECU`'s new WINDOW_STATUS (0x1A1) and LIGHTING_STATUS
    (0x1A2) messages, and `CabinECU`'s new BLIS_DATA (0x1B4).
- **Ignition (`xc90_sim.body.Ignition`)** — Volvo's distinctive rotary
  Start/Stop knob: OFF -> cranking -> RUN, plus an ACCESSORY position
  (infotainment/HVAC available, engine off). A real brake-to-start
  interlock (`start_engine()` no-ops without the brake pedal pressed,
  matching `MIN_BRAKE_FRAC_TO_START`) gates leaving OFF/ACCESSORY. This
  connects to everything that previously had no ignition concept to gate
  on: `Simulation.step()` now branches on `ignition.engine_running` before
  the gear-selector branch — off/accessory decays engine rpm toward 0
  (`Engine.step_off`, spin-down under internal friction, not instant),
  cranking ramps rpm up toward idle (`Engine.step_cranking`, simulating the
  starter motor) — either way zero driveshaft torque, same as
  Park/Neutral; infotainment and HVAC are force-powered-off whenever
  there's no accessory power, overriding whatever the driver last set;
  DRLs (`Lighting.drl_on()`) now require the engine actually running, not
  just headlights-off. `Simulation` exposes `start_engine()`/
  `stop_engine()`/`set_accessory_power()`. Every example/test entry point
  (`trip/runner.py`, `examples/zero_to_sixty.py`) had to add the
  brake -> start -> wait-for-crank sequence before shifting to Drive —
  a real breaking change from adding a real ignition state, not a bug.
- **Parking assist connected to the engine/drivetrain/steering** — closing
  a real gap: the previous pass built `ParkingAssist` and `SteeringSystem`
  as isolated pieces that never actually talked to the powertrain or to
  each other. Two connections now exist:
  - **Low-speed collision mitigation**, always active (not tied to any
    pilot feature): whenever `active_park_zone() == "critical"`,
    `Simulation.step()` forces throttle to 0 and applies an automatic
    brake (`PARK_ASSIST_AUTO_BRAKE_FRAC`) — overriding the driver's own
    pedal input, not just a dashboard tone. A real, simplified version of
    the low-speed autonomous braking Volvo's City Safety provides, not the
    full system (no camera/radar fusion, just the existing ultrasonic
    front/rear distance model).
  - **Park Assist Pilot** (`xc90_sim.cabin.ParkAssistPilot`) — genuine
    semi-autonomous parallel parking, the deeper connection: a side-facing
    distance sensor (separate from the front/rear `ParkingAssist` sensors)
    scans for a gap while driving past (`start_park_pilot_scan(side)` +
    `set_park_pilot_side_obstacle_m()`); once a gap of at least
    `PARK_PILOT_MIN_SPOT_LENGTH_M` is found and the driver shifts to
    Reverse and calls `engage_park_pilot()`, the pilot takes over
    *steering* for real — `Simulation.step()` reads
    `steering_command_deg()` instead of the driver's own input while
    maneuvering — through a genuine two-phase geometric technique: full
    lock toward the curb and reverse until the heading has rotated
    `PARK_PILOT_PHASE1_HEADING_DEG` (~35°), then full lock the other way
    and reverse back to parallel (`PARK_PILOT_COMPLETE_HEADING_TOLERANCE_
    DEG`) — the same "turn to lock, reverse to an angle, countersteer to
    straighten" technique driving instruction describes for a human doing
    this by hand, not Volvo's actual (proprietary, unpublished) path-
    planning algorithm. Throttle/brake during the maneuver is an
    automatic slow creep (reusing `CruiseController`'s proportional
    controller — mutually exclusive with real cruise control since one
    requires Drive and the other Reverse, so sharing the instance is
    safe), not the driver's pedal. Real safety behavior throughout: a
    close obstacle during the maneuver aborts it immediately
    (`phase = "aborted"`), and the driver can cancel at any time — a firm
    brake press or leaving Reverse both hand control straight back,
    checked every tick in `Simulation.step()`. Tested end-to-end (gap
    scan -> engage -> phase 1 -> phase 2 -> complete, plus the abort and
    cancel paths) — see `xc90_sim/cabin/park_assist_pilot.py`.
- **Engine Auto Start/Stop** (`xc90_sim.electrical.AutoStopStart`) — shuts
  the engine off at a stop to save fuel and restarts it automatically,
  explicitly modeled as a DIFFERENT thing from the ignition itself: while
  auto-stopped, `Ignition.state` stays `"run"` and accessory power is
  completely unaffected — only the engine stops turning. Engages once
  essentially stationary, in Drive/Neutral, with the brake held past
  `AUTO_STOP_MIN_BRAKE_FRAC_TO_ENGAGE`; resumes the instant the brake
  releases below `AUTO_STOP_RESUME_BRAKE_FRAC` or the gear leaves D/N.
  Restart reuses `Engine.step_cranking()` but with a much shorter
  `AUTO_STOP_RESTART_TIME_S` than a cold start's `STARTER_CRANK_TIME_S` —
  real auto-stop systems restart far faster than a full starter-motor
  crank. Driver-disableable per trip (`set_auto_stop_start_enabled()`),
  same as a real dash button. Tested: engages at a stop, holds through
  the stop with accessories confirmed still available, resumes cleanly on
  brake release, and stays off entirely when disabled.
- **Wipers** (`xc90_sim.body.Wipers`) — front (off/intermittent/low/high)
  and rear tailgate-glass (off/intermittent/on) wiper speeds, each with a
  real sweep-cycle timer (`front_sweeping()`/`rear_sweeping()` report
  whether a physical wipe is happening right now vs. the pause between
  sweeps at intermittent speed) rather than just an on/off flag. Broadcast
  via `BodyECU`'s new WIPER_STATUS (0x1A3).
- **Panoramic sunroof** (`xc90_sim.body.Sunroof`) — the glass panel
  (closed/vent/open) and the electric sunshade/cover move independently
  but with a real mechanical interlock: requesting the glass open
  auto-opens the shade first (the glass panel retracts into the same
  space the shade occupies in a real sunroof), and the shade can't close
  while the glass isn't fully closed — both no-op the wrong request rather
  than silently doing something impossible. Both actuate on a timed cycle
  (`SUNROOF_GLASS_ACTUATION_TIME_S`/`SUNROOF_SHADE_ACTUATION_TIME_S`), same
  technique as the power tailgate. Broadcast via `BodyECU`'s new
  SUNROOF_STATUS (0x1A4). Tested: glass-open forces the shade open first;
  closing the shade while the glass is open is correctly blocked.
- **Seat fold-flat mechanism connected to cargo capacity** — `Seat.
  can_fold_flat` is true only for the 2nd/3rd row (front seats don't fold
  flat); folding a seat vacates it (`occupied`/`seatbelt_buckled` both
  forced False — a real folded seat isn't a usable seat shape), and
  trying to occupy an already-folded seat is refused. `Storage.
  available_cargo_volume_l(seating)` connects this to the two real
  published Volvo figures (314L behind the 3rd row, 1,858L with 2nd/3rd
  folded flat) — returns the max figure only once every fold-flat seat
  actually is folded, the conservative figure otherwise; partial-fold
  configurations aren't published, so this doesn't try to interpolate one.
- **TPMS (Tire Pressure Monitoring System)** (`xc90_sim.cabin.TPMS`) — a
  real safety feature that was genuinely missing, not a cosmetic add: each
  wheel's pressure vs. `RECOMMENDED_COLD_PRESSURE_PSI`, warning at the
  actual FMVSS 138 federal threshold (25% below recommended, not a guess —
  see `TPMS_WARNING_THRESHOLD_FRAC`). Broadcast via `CabinECU`'s new
  TPMS_DATA (0x1B5). `RECOMMENDED_COLD_PRESSURE_PSI = 36.0` is a commonly
  cited figure for this class/tire size, not independently verified for
  this exact trim/wheel combination — flagged ASSUMPTION.
- **Oil life monitor** (`xc90_sim.cabin.OilLifeMonitor`) — a miles-since-
  reset countdown, explicitly modeled as what a real oil life monitor
  actually is (NOT a continuous oil-quality sensor most cars don't have):
  a technician resets it via a service menu after an actual oil change
  (`reset_oil_life()`). Defaults to fresh (0 miles since reset) rather
  than fabricating a "last changed" mileage, since `service_history.py`'s
  real CARFAX source has no recorded oil-change events to seed one from
  (CARFAX often doesn't capture quick-lube oil changes) — an honest gap,
  not a silently invented one. Fed real accumulated distance each tick
  from `body.distance_m` (already a proper odometer via `math.hypot`, so
  this can't drift out of sync with it). Broadcast via `CabinECU`'s new
  MAINTENANCE_DATA (0x1B6). Verified the countdown math is exact (0.56 mi
  driven -> life dropped by exactly 0.0056 percentage points of the
  10,000-mile interval) and that reset restores exactly 100%.
- **Infotainment touchscreen menu screens** (`Infotainment.SCREENS`:
  home/media/nav/climate/park_assist/seats/car_status) — Climate, Park
  Assist, Seats (including per-seat head-restraint state), and Car Status
  (oil life, tire pressure) are real navigable menu pages mirroring
  Volvo's actual Sensus touchscreen structure, not just backend methods
  with no UI home. `Simulation.infotainment_screen_data()` composes
  whichever subsystem's status the current screen needs (HVAC/
  ParkingAssist+ParkAssistPilot/Seating/TPMS+OilLifeMonitor) — same
  "aggregate at the Simulation level, don't couple the leaf class to
  everything else" pattern as `active_park_zone()`, so `Infotainment`
  itself stays standalone/testable.
- **Cylinder-level combustion engine** — replaced the empirical torque-curve
  lookup `Engine` used internally with a genuine 4-cylinder thermodynamic
  model (`xc90_sim/engine/cylinder.py`, `camshaft.py`), while keeping
  `Engine`'s exact public interface (`rpm`/`omega`/`throttle`/
  `step_locked`/`step_unlocked`/`step_off`/`step_cranking`/
  `set_throttle`) unchanged — nothing downstream (torque converter,
  transmission, `Simulation.step()`) needed to change.
  - **Real per-cylinder thermodynamics**: piston position from slider-crank
    geometry (using the *verified* bore 82.0mm / stroke 93.2mm for the
    Drive-E B4204T9 — self-consistent with this project's published 1.969L
    displacement to 4 significant figures), a real camshaft-timed 4-stroke
    cycle with genuine intake/exhaust valve overlap (not the idealized
    "one valve closes exactly when the other opens" simplification), and
    combustion via the standard single-zone Wiebe heat-release ODE
    (`dP = [(gamma-1)*dQ - gamma*P*dV]/V`, the same equation real
    simplified engine-simulation tools use, not CFD/multi-zone but genuine
    first-law thermodynamics). Indicated torque comes from actually
    integrating gauge pressure through the piston's real geometric motion
    (`torque = gauge_pressure * dV/dtheta`), not an assumed shape.
  - **Real twincharger boost model**: supercharger boost is instant and
    rpm-proportional (belt-driven, no lag); turbo boost genuinely lags
    toward its target via `BOOST_LAG_TAU_S` — the real physical reason
    boost lag exists (exhaust-energy-driven spool-up) — with the handoff
    between them using the actual researched rpm points from this
    project's earlier forum research pass. Fuel injection is real too:
    trapped air mass from the ideal gas law (MAP, volumetric efficiency,
    charge temperature) times a target AFR that richens under boost (real,
    documented ECU tuning practice, stoichiometric 14.7 at light load
    toward ~12.3 at full boost) — this is where `Engine.
    total_fuel_burned_kg` (feeding the fuel tank, below) actually comes
    from, not an assumed MPG figure.
  - **Calibrated against the real published torque/power curve** (2026-08-
    22): a virtual dyno sweep (`Engine.wide_open_torque_nm()`, side-effect-
    free — runs throwaway scratch cylinders, never disturbs the real
    firing engine) lands within ~5% of the published ~400Nm flat torque
    plateau (2200-5400rpm) and within 1% of the published 316hp@5700rpm
    peak power, achieved by tuning the supercharger/turbo boost split to
    stay close together (a real ECU deliberately tapers available boost to
    hold torque flat via wastegate control, rather than letting torque
    climb with whatever the turbo has "available" at higher rpm — a real
    tuning concept this calibration had to reproduce, not just a number
    hunt).
  - **Two real bugs caught by testing**, not left silently: (1) a
    multi-cylinder charge-trapping bug — a cylinder whose phase offset
    happened to start it mid-combustion incorrectly triggered a
    "just-crossed-IVC" charge trap using the wrong (near-TDC) volume,
    corrupting that cylinder's first cycle; fixed by only ever trapping a
    charge after a cylinder has genuinely visited its own intake regime.
    (2) A fixed sub-step count that was fine-grained enough at
    `zero_to_sixty.py`'s small dt (500Hz) silently became far too coarse
    at `run_trip.py`'s dt (50Hz) — at typical cruise rpm that's ~29 crank-
    degrees per sub-step, aliasing right past the ~50-degree-wide
    combustion event and destabilizing the pressure ODE into oscillation,
    stalling the engine during a sustained partial-throttle cruise test
    (a full-throttle launch never exposed it, since its dt was already
    fine enough) — fixed by making the sub-step count adaptive to a target
    crank-degrees-per-substep instead of a fixed count. (What looked like
    a third bug — the engine "stalling" to 0rpm while stopped — turned out
    to be Engine Auto Start/Stop correctly doing its job during a test
    that left the brake held down; not a bug.)
  - **Honest remaining gap**: simulated fuel economy at a steady highway
    cruise (55mph) comes out around 50mpg — roughly 2x better than this
    car's real EPA highway rating (~25mpg). The road-load physics checks
    out exactly (12.15kW needed at 55mph, matching hand-calculation from
    the same drag/rolling-resistance constants used elsewhere in this
    project) and the torque converter is confirmed locked (no slip loss)
    at that operating point, so the gap is in the engine's own part-load
    efficiency: real engines get meaningfully *less* efficient at very
    light load (a small fraction of the engine's capability) than at
    their best-efficiency operating point, a "BSFC map" effect this
    project's simple quadratic friction curve doesn't fully capture. A
    real, named parasitic load (`ACCESSORY_LOAD_NM_AT_1000_RPM` —
    alternator/power-steering/AC-compressor draw, genuinely absent before
    this rewrite) was added and is real, but is far too small (~0.4kW) to
    close a 2x gap on its own. Flagged honestly rather than force-fit with
    an undocumented fudge factor; full-throttle calibration (where this
    project's testing has focused, and where the numbers matter most for
    0-60/quarter-mile figures) is unaffected and matches published data
    closely.
  - **Timing belt (not chain) + accessory belt**: real, verified (2026-08-
    22, multiple independent sources) — the Drive-E B4204 uses a timing
    BELT, due at 150,000mi/12yr — added to `wear/wear_model.py`'s
    `WEARABLE_COMPONENTS` with `floor_condition=1.0` (a belt doesn't
    gradually degrade performance the way tires/brakes do — it's fine
    until it isn't — so this exists purely for maintenance-due tracking
    via the new `WearModel.service_due()`, not to scale any physics).
    Accessory/serpentine belt added the same way with an ASSUMPTION-
    flagged interval (not documented in this car's real service history).
  - **Real fuel tank** (`xc90_sim.fuel_system.FuelTank`): capacity 71L/18.8
    gal, the actual published Volvo spec (volvocars.com support, checked
    2026-08-22), drawn down by real fuel mass burned (`Engine.
    total_fuel_burned_kg`'s delta each tick — same pattern as the odometer/
    oil-life tracking), not an estimated MPG figure layered on top. Low-
    fuel warning, refueling (`add_fuel_l()`), broadcast via `CabinECU`'s
    extended MAINTENANCE_DATA.
  - **New engine sensor**: a MAP (intake manifold absolute pressure)
    sensor reading — a real, standard OBD2 PID (0x0B) — with realistic
    measurement noise, added to `ENGINE_DATA`, reading the genuine
    combustion-model manifold pressure rather than an assumed constant.
    (Crank position itself continues to come directly from the physics
    state, not through a separate quantized sensor model the way wheel
    speed gets — an intentional scope boundary, not an oversight.)
- **Every remaining engine/drivetrain part reified as a real, connected
  component** (2026-08-23) — a direct response to being asked "is X
  actually written, or just implied": fuel injectors, the timing belt, the
  accessory belt, the alternator, the fuel pump, and the intake/exhaust
  valves were all previously either invisible math inside `Cylinder`, a
  bare constant, or (for the electrical system) not modeled at all. All
  now exist as their own classes, spread across `xc90_sim/engine/` (the
  valves and timing belt), `xc90_sim/fuel_system/` (fuel injectors, fuel
  pump), and `xc90_sim/electrical/` (accessory belt, alternator) — and,
  the part that actually matters, each one is functionally wired in, not
  just decorative:
  - **`Flywheel`**: its own inertia is DERIVED (`I = 0.5*m*r^2`) from an
    assumed mass/radius, not a bare guess — split out of the old single
    `CRANK_INERTIA_KGM2` constant into `FLYWHEEL_INERTIA_KGM2` +
    `OTHER_ROTATING_INERTIA_KGM2` (crank pins/rod big-ends/pulleys/damper)
    that sum to exactly the same total, so this adds real component-level
    detail without silently changing the already-calibrated physics.
    `Engine.total_rotating_inertia_kgm2` (flywheel + other) is what
    `step_unlocked`/`step_off` actually integrate against now.
  - **`TimingBelt`**: the real 2:1 camshaft:crankshaft ratio (exact for
    any 4-stroke engine, not an assumption) is now an explicit,
    genuinely-computed conversion (`Engine.camshaft_angle_deg`), not an
    implicit byproduct of how `cycle_angle_deg` happens to be tracked. A
    worn belt causes a small camshaft timing retard — real behavior — but
    with `floor_condition=1.0` on `wear_model.py`'s "timing_belt" entry,
    `condition` can never actually drop below 1.0, so this retard is
    currently a genuine, wired-up no-op rather than a fake number; honest
    about that rather than hiding it.
  - **`AccessoryBelt` + `Alternator`**: this is the connection that
    actually matters — real electrical demand from whatever's genuinely
    switched on (headlights, HVAC blower, active seat heaters,
    infotainment, wipers, the fuel pump's own draw) is computed every tick
    in `Simulation.step()` and fed to `Engine.set_electrical_demand_w()`,
    which the alternator converts to a real crank-torque draw — replacing
    what used to be one flat, always-on constant. Verified directly:
    turning on headlights + max HVAC fan + a heated seat (390W combined,
    computed exactly from the real per-item wattages) measurably dragged
    idle rpm down from 1067 to 947 in testing — a real, physically
    correct effect, not a decorative object that exists but does nothing.
    The AC compressor is a separate, mechanical (belt-driven) load,
    engaged only while HVAC is actually calling for active cooling, not
    just because the AC button is on. This car has ELECTRIC power
    steering (see specs/steering.py) — deliberately did NOT add a belt-
    driven hydraulic steering pump, which would contradict that.
  - **`FuelPump`**: a real electric lift pump feeding a camshaft-driven
    high-pressure pump (this is a genuine direct-injection/GDI engine),
    with fuel rail pressure that builds over real time (~0.6s) once the
    ignition calls for it — verified it reaches its full 150 bar target
    by the time cranking completes — and bleeds down when off. Low
    pressure would derate injector flow (a real GDI coupling), and the
    pump itself is a real electrical load on the alternator.
  - **`FuelInjector`** (one per cylinder): converts the commanded fuel
    mass into an actual pulse width in milliseconds via a rated flow rate
    — the real quantity an ECU computes and commands, not fuel mass
    appearing from nowhere. Verified producing realistic sub-2ms pulse
    widths at light load. Exposed via telemetry
    (`injector_pulse_width_ms`).
  - **`Valve`** (real DOHC 4-valve-per-cylinder layout — 2 intake + 2
    exhaust per cylinder, `specs.cylinder.INTAKE_VALVES_PER_CYLINDER`/
    `EXHAUST_VALVES_PER_CYLINDER`): a genuine raised-cosine lift curve
    (0 at open/close, peak at mid-duration — the standard simplified
    shape when a real cam profile isn't published), not just an
    open/closed boolean. `Camshaft` now owns real `Valve` instances and
    delegates to them, rather than having the open/closed timing math
    inlined as bare functions. (The lift *magnitude* isn't yet used to
    compute a flow restriction — this sim still treats an open valve as
    "cylinder pressure tracks manifold pressure" regardless of exactly how
    far open it is — an honest scope boundary, not an oversight.)
- **Whole-car parts audit (2026-08-23)**: asked directly whether every car
  part existed, not just the engine. Found and fixed one real logical
  inconsistency (an `Alternator` charging a `Battery` that didn't exist)
  plus several genuinely-missing lighting/electrical parts:
  - **`Battery`** (`xc90_sim.electrical.Battery`) — 12V AGM (a real,
    well-known requirement for a car with genuine Auto Start/Stop; a
    flooded lead-acid battery wears out prematurely under that much
    engine-off/restart cycling). Charges (a small maintenance trickle)
    while the alternator's actually supplying power, discharges to cover
    accessory-only demand or the real current spike a starter motor draws
    while cranking. A genuine connected failure mode, not just a
    dashboard number: `start_engine()` now fails if the battery's too
    weak to crank — verified directly (a battery forced to 5% charge
    correctly blocks starting; a normal one drains slightly during
    cranking then recovers while running).
  - **Brake lights / reverse lights** — real, and deliberately NOT driver-
    settable: `Simulation.step()` sets them from the actual brake pedal
    and gear selector each tick, the same "compose at the Simulation
    level" pattern as `active_park_zone()`. Verified: brake lights track
    the brake pedal specifically (not throttle), reverse lights track
    gear R specifically.
  - **Fog lights, interior dome light, horn** — fog lights are a plain
    driver toggle; the dome light is real composed state (automatic on
    real door-open, same pattern as brake lights, OR a manual override) —
    verified both paths independently; the horn is a simple momentary
    circuit. All three are real electrical loads on the alternator now
    (see below), not free.
  - **Windshield washer fluid** (`xc90_sim.body.WasherFluid`) — a small
    real consumable, depleted by actual spray events, with a low-level
    warning.
  - Horn, fog lights, and dome light all feed into the same real
    electrical-demand calculation the alternator/battery already use
    (see the "AccessoryBelt + Alternator" entry above) — turning them on
    is not free, same as everything else on that list.
  - **Second pass: all five gaps above closed (2026-08-24)** — cooling
    system, exhaust system (plus turbocharger reification, O2 sensors,
    EGR, exhaust backpressure), drivetrain hardware (propshaft,
    transmission fluid, CV joints, wheel bearings), airbags/SRS, and
    radar-based ADAS (adaptive cruise + lane-keeping assist) are all now
    real, connected, tested components — see the five subsections
    directly below ("Cooling system", "Exhaust system...", "Drivetrain
    hardware reification", "Airbags/SRS", "Radar-based ADAS") for full
    architecture writeups. All wired into `sim/simulation.py` and
    verified against this project's own regression suite
    (`examples/zero_to_sixty.py`, `examples/run_trip.py`) throughout: 0-60
    ≈6.34s, 1/4 mile ≈14.68s @ 100.6mph — unchanged across all five
    additions, as expected (none of them touch the straight-line
    drivetrain torque path in a way that should move those numbers).
- **Third pass: 6 of the 7 scope boundaries the second pass surfaced,
  closed (2026-09-01)** — the second pass above built five whole real
  systems but honestly flagged its own edges (see "Left to do"'s old
  "Scope boundaries..." list); this pass went back and closed six of
  those seven: propshaft windup closed back into the torque path (with a
  real torsional-stiffness bug caught and fixed along the way — see "Bugs
  found and fixed"), a real water pump/coolant-flow-rate model, the
  transmission cooler reified as its own airflow-dependent object,
  Occupant Classification System child-seat detection, SRS self-test/
  bulb-check diagnostics, and a second (thermal/gamma) EGR dilution
  mechanism alongside the existing displacement one — full writeups
  folded into each item's existing subsection below. The seventh
  (real ACC/LKA traffic/lane geometry, as opposed to the existing
  externally-driven virtual sensors) was deliberately NOT attempted —
  see "Left to do" for why that one is a permanent scope boundary, not a
  deferred TODO. Verified against this project's own regression suite
  throughout: 0-60 stays 6.34-6.35s, 1/4 mile 14.69-14.70s @ 100.4mph —
  unchanged from baseline, as expected (none of these six touch the
  straight-line drivetrain torque path in a way that should move those
  numbers; the propshaft windup closure was the one change with a real
  chance of moving them, and didn't).
- **Cooling system** (`xc90_sim.cooling.CoolingSystem`, `specs/cooling.py`)
  — closes the first item from the audit above: engine thermal state is
  real now, not just its rotational/combustion physics. `CoolingSystem.
  step(dt, fuel_energy_rate_w, vehicle_speed_mps, ambient_temp_c)` evolves
  `coolant_temp_c` from real heat in vs. heat rejected. Heat in is
  `COOLANT_HEAT_FRACTION_OF_FUEL_ENERGY` (0.30 — real engines send roughly
  a third of fuel chemical energy to the coolant) times `fuel_energy_rate_w`,
  which `Simulation.step()` computes every tick from the engine's own real
  fuel-mass-burned delta (`fuel_burned_delta_kg * FUEL_LHV_J_PER_KG / dt`,
  gasoline LHV 44.0e6 J/kg) — not an assumed heat-output constant. The
  thermostat opens at `THERMOSTAT_OPEN_TEMP_C` (90°C) with 3°C hysteresis,
  blocking radiator flow while cold so warm-up isn't slowed by rejecting
  heat immediately — real behavior, not just a nice-to-have detail. The
  electric fan cycles on/off with its own hysteresis band (`FAN_ON_TEMP_C`
  100°C / `FAN_OFF_TEMP_C` 96°C, a few degrees apart specifically to avoid
  rapid on/off cycling). Radiator rejection scales with real airflow:
  proportional to vehicle speed up to a ~30 m/s ram-air saturation point,
  or a stationary fraction (`RADIATOR_STATIONARY_DISSIPATION_FRAC` = 0.25)
  when idling with the fan running — genuinely less cooling available
  stopped than at speed, same as a real car. Passive ambient heat loss
  (`AMBIENT_HEAT_LOSS_W_PER_K`) always applies, even with the thermostat
  closed. `heating_available_frac()` ramps 0→1 between a cold floor
  (thermostat-open-temp minus 20°C) and `NORMAL_OPERATING_TEMP_C` (95°C),
  feeding `HVAC.step()`'s new `heating_available_frac` parameter so cabin
  heat output realistically ramps in over the engine's warm-up — the
  classic real "car heater takes a few minutes" experience — while
  cooling/AC output is completely unaffected by coolant temperature, same
  as a real AC compressor not caring how warm the engine is. ASSUMPTION
  throughout (no published cooling-system specs exist for this exact car),
  but sized/tuned against the sim's own real fuel-flow output rather than
  guessed in isolation — see the radiator-sizing bug below.
  - **Real water pump / coolant flow-rate model** (2026-09-01,
    `xc90_sim/cooling/water_pump.py`, `WaterPump`) — closes the "no water
    pump or flow-rate model" gap the second pass flagged. This engine uses
    a genuine ELECTRIC coolant pump (Volvo part 32382249, confirmed via
    this project's own parts_catalog research), not a belt-driven
    mechanical one — letting the ECU vary flow independently of engine
    rpm, real behavior a belt-driven pump can't reproduce. Flow is
    near-zero during cold start (a `WATER_PUMP_WARMUP_START_C` = 40°C
    floor at `WATER_PUMP_MIN_WARMUP_FLOW_FRAC` = 0.15), ramping to full
    flow by `WATER_PUMP_FULL_FLOW_C` (75°C) or immediately under high load
    (`throttle > 0.6`); after a hot shutdown (coolant ≥100°C), the pump
    keeps running for up to `WATER_PUMP_POST_SHUTDOWN_RUN_S` (60s) — real
    "heat soak" protection against localized boiling around the turbo, a
    genuine feature of electric pumps on turbocharged engines. A `failed`
    flag (settable via `Simulation.set_water_pump_failed()`) zeroes flow
    entirely regardless of demand — a genuine, severe overheat failure
    mode: verified with a failed pump, coolant ran away from 88°C to
    284°C over 100s even at highway speed with the fan running, since
    nothing is circulating through the radiator at all. `CoolingSystem.
    step()` gained a `coolant_flow_frac=1.0` parameter multiplying
    radiator rejection (`radiator_reject_w = ... * airflow_frac *
    coolant_flow_frac`) — radiator effectiveness now genuinely depends on
    BOTH airflow (existing) and coolant flow (new); either one being
    starved limits heat rejection. `Simulation` constructs
    `self.water_pump = WaterPump()`, steps it each tick (before
    `cooling_system.step()`) from real coolant temp/engine-running/
    high-load state, and feeds its `flow_frac` into `cooling_system.
    step()`. All new constants ASSUMPTION (not published for this car).
    Verified: flow ramps from ~0.6% at cold start to ~100% by the time
    coolant reaches ~83°C during a warm-up+cruise test; regression suite
    unaffected (0-60 6.34s). New telemetry: `coolant_temp_c`,
    `thermostat_open`, `cooling_fan_on`, `engine_overheating`,
    `water_pump_flow_pct`, `water_pump_failed`.
- **Exhaust system, turbocharger reification, O2 sensors, EGR, exhaust
  backpressure** (`xc90_sim.exhaust.ExhaustSystem`/`Turbocharger`/
  `OxygenSensor`/`EGRValve`, `specs/exhaust.py`) — closes the second item
  from the audit above (manifold/catalytic converter/muffler/O2 sensors
  were never addressed at all before this).
  - `ExhaustSystem` models catalytic converter light-off: `catalyst_temp_c`
    heats toward `EXHAUST_GAS_TEMP_C` (650°C, ASSUMPTION) on a real
    first-order thermal lag (`CATALYST_HEATUP_TAU_S` = 20s — a small
    ceramic substrate, heats up fast once exhaust actually flows) while
    the engine's running, and decays back toward ambient when it's not.
    `catalyst_active()` only reports true once `catalyst_temp_c` crosses
    `CATALYST_LIGHT_OFF_TEMP_C` (300°C) — the real reason cold-start
    emissions are worse than warmed-up emissions: a cold catalyst doesn't
    convert pollutants effectively yet.
  - `Turbocharger` is a real reification, not new physics: this exact
    boost-lag logic used to live as an inline `turbo_boost_pa` attribute
    plus an `_update_turbo_boost()` method directly on `Engine`; both are
    gone now, replaced by a named `Turbocharger` object with its own
    `step(dt, rpm, throttle)`/`reset()`, and `Engine._combined_boost_pa()`
    now reads `self.turbocharger.boost_pa` instead of an inline attribute.
    This is the exhaust-driven, laggy half of the twincharger system (the
    supercharger half stays instant/rpm-proportional/belt-driven,
    unchanged) — same physics as before this pass, now owned by its own
    component instead of living as bare `Engine` attributes.
  - `OxygenSensor` (one per cylinder — `Engine.oxygen_sensors`, a list of
    4) reads the real per-cylinder AFR the combustion model actually
    computed, converts it to lambda (1.0 = stoichiometric), and applies a
    first-order response lag (`O2_SENSOR_RESPONSE_TAU_S` = 0.15s — real O2
    sensors aren't instant) plus Gaussian measurement noise
    (`O2_SENSOR_NOISE_STD_LAMBDA`) — the same "real sensors aren't
    perfect" treatment this project already gives `WheelSpeedSensor`.
  - `EGRValve` models exhaust gas recirculation as a reduction in
    effective trapped fresh charge — a volumetric-efficiency derating,
    since recirculated exhaust gas physically displaces fresh intake air
    in the same manifold volume, the real mechanism — rather than a full
    multi-species thermodynamic dilution model. A deliberate
    simplification, documented as such, not an oversight. Real
    qualitative behavior is preserved: `flow_fraction` ramps up toward
    `EGR_MAX_FLOW_FRACTION` (0.12) at light/mid load within a cruise rpm
    band (`EGR_MIN_RPM`-`EGR_MAX_RPM`, 1200-3500), and is forced to 0
    outside that rpm band or above half throttle — matching why real ECUs
    shut EGR off at idle and under load, where it would hurt
    driveability/power.
  - **Second real dilution mechanism added (2026-09-01): the thermal
    (gamma) effect, alongside the existing displacement effect above.**
    Recirculated exhaust gas (mostly triatomic CO2/H2O) has a lower
    specific-heat ratio (gamma) than fresh air, which affects the
    compression-phase pressure trace — a real mechanism this project
    hadn't modeled at all before, distinct from the displacement/VE-
    derating mechanism above. `specs/cylinder.py` gained
    `DILUTED_CHARGE_GAMMA_MIN = 1.30` (vs. `INTAKE_GAMMA = 1.35`),
    ASSUMPTION, representing a fully-diluted charge's lower gamma.
    `Cylinder.step()` gained a `dilution_frac=0.0` parameter; during the
    compression regime, gamma is now blended: `diluted_intake_gamma =
    INTAKE_GAMMA - dilution_frac * (INTAKE_GAMMA -
    DILUTED_CHARGE_GAMMA_MIN)`. `Engine._cylinder_torque_sum_nm()`
    computes `dilution_frac = egr_valve.flow_fraction + pcv_valve.
    ve_derate_fraction()` (folding in the pre-existing PCV dilution too)
    and passes it into each cylinder's `step()` call alongside the
    existing, unchanged `ve_frac` computation for the displacement
    mechanism. Still explicitly a simplification, not a full
    multi-species treatment — there's no separate tracked species/
    composition/heat-capacity through the combustion energy balance, just
    one blended effective gamma, documented honestly as such in
    `egr_valve.py`'s own docstring rather than overclaimed as "fully
    solved." Verified: EGR is gated off entirely above throttle>0.5 by
    pre-existing logic, so this could not possibly affect the 0-60/
    quarter-mile regression by construction; checked separately via a
    light-throttle cruise test producing sane telemetry (no NaN/
    instability), and the full `run_trip.py` regression (which does
    exercise EGR during light cruise) matched baseline.
  - Real exhaust backpressure (`BACKPRESSURE_PA`, ~0.08 bar, ASSUMPTION)
    now feeds back into the physics, not just a display number:
    `Cylinder.step()` gained a `backpressure_pa=0.0` parameter, and
    exhaust-stroke pressure is now `ATMOSPHERIC_PRESSURE_PA +
    backpressure_pa` instead of bare atmospheric — a small, real negative
    (pumping-loss) torque contribution during the exhaust stroke, the
    genuine mechanism by which a restrictive exhaust costs an engine
    power.
  - New telemetry: `catalyst_temp_c`, `catalyst_active`,
    `o2_sensor_lambda`, `egr_flow_fraction`, `turbo_boost_bar`.
- **Drivetrain hardware reification** (`xc90_sim.drivetrain.Propshaft`/
  `CVJoint`/`WheelBearing`, `xc90_sim.transmission.TransmissionFluid`) —
  closes the third item from the audit above. Wheel bearings, transmission
  fluid/cooler, and propshaft/CV joints are now real, named, connected
  objects — constructed once from real wear conditions at `Simulation()`
  construction time, same
  "evaluated once, not re-computed every tick" pattern already used for
  tire grip/brake pad condition.
  - `Propshaft` gets real torsional windup: `windup_angle_rad` is
    genuinely computed each tick from real rear-axle torque (target =
    `rear_torque_nm / TORSIONAL_STIFFNESS_NM_PER_RAD`, approached via a
    fast `RESPONSE_TAU_S` = 0.02s lag).
  - **Windup closed back into the torque loop (2026-09-01)** — closes the
    "telemetry-only" gap the second pass flagged. `delivered_torque_nm()`
    (`= TORSIONAL_STIFFNESS_NM_PER_RAD * windup_angle_rad`) reads the
    shaft's own lagged torsional-twist state back out as a real torque.
    `Simulation.step()` now runs `self.propshaft.step(dt,
    rear_drive_torque)` immediately after `HaldexAWD.split()`, then
    reassigns `rear_drive_torque = self.propshaft.delivered_torque_nm()`
    before feeding it into `self.rear_diff.split()` — the rear
    differential (and everything downstream: CV joints, rear wheels) now
    receives the shaft's real lagged/twisted torque instead of the
    instantaneous commanded value. At steady state this exactly equals the
    commanded torque (windup settles to torque/stiffness); only
    *transients* (a hard launch, a gearshift) see the shaft's compliance
    smooth/delay delivery by roughly its `RESPONSE_TAU_S` (0.02s). This is
    a first-order approximation of the propshaft's dominant torsional
    mode, not a full re-derivation of the multi-body AWD driveline
    (propshaft inertia interacting with the Haldex clutch and differential
    dynamics in full generality) — that fuller treatment remains out of
    scope, now documented as such in `propshaft.py`'s own docstring.
  - **Bug found and fixed before closing the loop** (see "Bugs found and
    fixed" below for the full writeup): `TORSIONAL_STIFFNESS_NM_PER_RAD`
    had been 8000 Nm/rad since this was first introduced telemetry-only,
    which produced ~40° of windup at this car's peak simulated rear-axle
    torque during a hard launch — wildly unrealistic (real steel propshaft
    windup is a few degrees at most, even at peak torque). Re-derived from
    G*J/L for a plausible tubular steel propshaft (G=79 GPa, ~70mm OD/64mm
    ID, ~1.5m length): computed k≈37,000 Nm/rad, rounded to 40,000 Nm/rad
    — now produces ~8-9° of windup at peak torque, a defensible range for
    this class of shaft. Found and fixed *before* closing the loop — it
    would have been a much worse bug once closed, since the torque path
    would have been distorted by an unrealistically soft spring. Verified:
    max windup during a hard launch dropped from ~40° (bug) to ~8.3°
    (fixed) before closing the loop; regression suite unaffected after
    closing it (0-60 6.33-6.34s, unchanged); `run_trip.py`'s Haldex
    front-bias average shifted slightly (73-74% → ~75%), a small,
    plausible, non-alarming effect of the propshaft now smoothing
    rear-torque transients slightly. `windup_angle_rad` stays available as
    telemetry (`propshaft_windup_deg`) alongside the new
    `delivered_torque_nm()`.
  - `TransmissionFluid` temperature is driven by real torque-converter
    slip-loss heat — computed as `abs(pump_load * engine.omega -
    turbine_torque * real_turbine_omega)`, the actual power difference
    between what the pump absorbs and what the turbine delivers while the
    converter is unlocked, a genuine physical heat source, not an assumed
    one — cooled by a real cooler term proportional to the fluid-to-
    ambient temperature difference. `condition` comes from the wear model
    (same maintenance-due tracking as the timing/accessory belts — it
    doesn't scale any physics itself, the fluid's own real temperature
    does that). `overheating()` flags past `OVERHEAT_WARNING_TEMP_C`
    (120°C, ASSUMPTION).
  - **Transmission cooler reified as its own object (2026-09-01,
    `xc90_sim/transmission/transmission_cooler.py`, `TransmissionCooler`)**
    — closes the "fixed dissipation coefficient" gap the second pass
    flagged. Replaces what used to be `TransmissionFluid`'s bare fixed
    constant (`COOLER_DISSIPATION_W_PER_K = 40.0`, now removed) with a
    genuine airflow-dependent `dissipation_w_per_k(vehicle_speed_mps)` —
    ram air, saturating at 30 m/s, the same technique as the engine
    radiator. Real detail modeled: unlike the engine radiator, a typical
    passenger-car transmission cooler has no fan of its own, so there's no
    fan-assisted stationary floor — just a small natural-convection floor
    (`TRANS_COOLER_MIN_DISSIPATION_W_PER_K` = 10 W/K) at a dead stop,
    ramping to `TRANS_COOLER_MAX_DISSIPATION_W_PER_K` (55 W/K) at speed,
    both in `specs/transmission.py`, ASSUMPTION. `TransmissionFluid.
    step()`'s signature changed from `(dt, slip_heat_w, ambient_temp_c)`
    to `(dt, slip_heat_w, ambient_temp_c, cooler_dissipation_w_per_k)` to
    take this real speed-dependent value instead of the old hardcoded
    module constant; `Simulation` constructs `self.transmission_cooler =
    TransmissionCooler()` and computes `dissipation_w_per_k(self.body.
    speed_mps)` into `transmission_fluid.step()` each tick. Verified:
    regression suite unaffected; transmission fluid temp stays near
    ambient during sustained highway cruise (torque converter locked
    ~91%+ of drive time, so little slip heat is generated outside
    launches/shifts — expected, not a bug).
  - `CVJoint` (one per front half-shaft — driven AND steered wheels need
    these to transmit power through a changing steering angle):
    `efficiency(steer_angle_rad)` returns a small, bounded loss that grows
    with steering angle (capped at `MAX_ANGLE_EFFICIENCY_LOSS_FRAC` = 3%)
    and with wear (`condition`, capped at `MAX_WEAR_EFFICIENCY_LOSS_FRAC`
    = 2%) — applied to front-drive torque in `Simulation.step()` after the
    differential split, sized to stay within real street-steering-angle
    magnitudes, not exaggerated.
  - `WheelBearing` (one per corner): `rolling_resistance_scale()` returns
    a modest, bounded multiplier (up to +10% at fully worn,
    `MAX_WEAR_RESISTANCE_INCREASE_FRAC`) applied via `VehicleBody`'s new
    `rolling_resistance_scale` constructor parameter, multiplied into
    `rolling_resistance_n()` — a worn bearing adds real drag, not a
    dramatic one.
  - `wear/wear_model.py`'s `WEARABLE_COMPONENTS` gained three new entries:
    `wheel_bearings` (120,000mi typical life / 0.95 floor condition —
    gradual real wear, unlike the belts, but bounded); `transmission_fluid`
    (60,000mi / floor 1.0, since it exists for maintenance-due tracking
    only — the fluid's own real temperature does the physics, not its
    wear-model condition); `cv_joints` (100,000mi / 0.95 floor, front-only
    since the rear isn't independently steered in this AWD layout). All
    three ASSUMPTION-flagged, since none of these intervals appear in this
    car's real service history.
  - New telemetry: `transmission_fluid_temp_c`,
    `transmission_fluid_overheating`, `propshaft_windup_deg`,
    `wheel_bearings_service_due`, `cv_joints_service_due`,
    `transmission_fluid_service_due`.
- **Airbags/SRS** (`xc90_sim.cabin.Airbag`/`AirbagSystem`, `specs/
  airbags.py`) — closes the fourth item from the audit above: safety-
  critical and completely absent before this pass.
  - `AirbagSystem.step(dt, ax_mps2, ay_mps2, power_on)` reads the REAL
    body-frame accelerometer data (`VehicleBody.ax_mps2`/`ay_mps2` — the
    exact signal the chassis ECU already reports as `accel_g`/
    `lateral_accel_g`), not a separate synthetic crash sensor (the `dt`/
    `power_on` parameters were added 2026-09-01 for the self-test timer,
    below — the signature was `step(ax_mps2, ay_mps2)` before that).
    Frontal deceleration past `FRONTAL_DEPLOY_THRESHOLD_G` (8.0g,
    ASSUMPTION — real thresholds are proprietary) deploys `driver_frontal`
    always, and `passenger_frontal` only if the front-passenger seat is
    occupied AND does not have a child seat installed — real Occupant
    Classification System behavior (an empty seat, or an occupied seat
    with a detected child seat, both suppress that airbag; see "Occupant
    Classification System: child seat detection" below). Lateral
    acceleration past `SIDE_DEPLOY_THRESHOLD_G` (5.0g) deploys the
    near-side thorax (side) bag and that side's full-length curtain bag.
    Any deployment fires seatbelt pretensioners for every occupied+buckled
    seat, checked against `xc90_sim.cabin.Seating`'s real per-seat state.
  - **Occupant Classification System: child seat detection (2026-09-01)**
    — closes the "doesn't detect child seats" gap the second pass flagged.
    `Seat` gained `child_seat_installed` state (default False, the same
    externally-driven pattern already used for `occupied`/
    `seatbelt_buckled`) plus a `set_child_seat_installed()` setter;
    `Simulation.set_child_seat_installed(seat_name, installed)` exposes
    it. The crash-sensing gate above now checks it directly — a detected
    child seat suppresses passenger-frontal deployment even while the
    seat reads occupied, the real OCS behavior. Verified via a synthetic
    crash test: occupied passenger seat without a child seat → passenger
    frontal deploys; same seat with a child seat installed → it doesn't
    (driver frontal still deploys normally in both cases).
  - `Airbag.deploy()` is one-time and permanent — real airbags are
    single-use pyrotechnic devices, no re-arming short of building a new
    `AirbagSystem`/`Simulation`.
  - **Honest ASSUMPTION**: real deployment algorithms integrate the shape
    of the crash pulse over tens of milliseconds against a "safing
    sensor," not a single instantaneous-g threshold — this sim has no
    collision/contact physics at all (no obstacles to actually crash
    into), so an instantaneous-g check against the real accelerometer
    signal is what's available here, not a crash-pulse-discriminating
    algorithm.
  - `any_deployed()`/`warning_light_on()`: the SRS warning light
    previously only reflected the "already deployed, needs service" case
    honestly.
  - **SRS self-test / bulb-check diagnostics (2026-09-01)** — closes the
    self-test gap the second pass flagged. A real power-on bulb-check
    timer (`_power_on_elapsed_s`, resets to 0 on a false→true `power_on`
    transition) now exists, alongside a `self_test_fault` flag (settable
    via `set_self_test_fault()` / `Simulation.
    set_srs_self_test_fault()`) representing a fault-injection hook for
    real diagnostic-trouble-code conditions this project doesn't simulate
    the wiring-level physics of (buckle-switch continuity, clockspring
    fault, etc.) — the same virtual-fault pattern already used for
    Relay/Fuse elsewhere in this project. `warning_light_on()` now returns
    true during the power-on bulb-check window
    (`SRS_BULB_CHECK_DURATION_S` = 3.0s, ASSUMPTION, in `specs/
    airbags.py`), OR if any airbag has deployed (existing, via
    `any_deployed()`), OR if `self_test_fault` is set (new) — previously
    it only covered the "already deployed" case. `Simulation`'s
    `airbag_system.step()` call site was updated to pass `dt` and
    `self.ignition.accessory_power` as `power_on`. Verified: light is on
    for the first 3 seconds after power-on, off after that with no fault;
    turns on immediately when `self_test_fault` is set.
  - Composed at the `Simulation` level (`self.airbag_system =
    AirbagSystem(self.seating)`, stepped right after `self.body.step()`
    with the real ax/ay just computed) — same "compose here, don't couple
    the leaf class to everything else" pattern as `dome_light_on`/
    `brake_lights_on`.
  - Verified: never fires during normal driving/hard braking (this
    project's own regression trip peaks around 0.6g longitudinal / 0.3g
    lateral, both well under the 8g/5g thresholds); fires correctly,
    including pretensioners, when given a synthetic crash-level
    deceleration in a standalone test.
  - New telemetry: `airbags_deployed` (list of deployed locations),
    `srs_warning_light`.
- **Radar-based ADAS: adaptive cruise control + lane-keeping assist**
  (`xc90_sim.cabin.ForwardRadar`/`AdaptiveCruiseController`/`LaneCamera`/
  `LaneKeepingAssist`, `specs/adas.py`) — closes the fifth and last item
  from the audit above; today's cruise control gains real follow-distance
  behavior and a real (if virtual-sensor-driven) lane-keeping steering
  nudge.
  - `ForwardRadar` is an externally-driven virtual sensor
    (`set_lead_vehicle(distance_m, relative_speed_mps)`/
    `clear_lead_vehicle()`) — this project has no real traffic simulation
    (no other vehicles with real positions), so this follows the exact
    same external-virtual-sensor pattern already established for
    `BlindSpotMonitor`/`ParkingAssist` (obstacle state set from outside).
  - `AdaptiveCruiseController.effective_target_speed_mps(radar,
    driver_set_speed_mps, own_speed_mps)`: no lead vehicle detected →
    returns the driver's plain set speed unchanged (falls through to being
    exactly the existing `CruiseController` — confirmed no regression).
    Lead vehicle detected → computes `desired_gap_m` from the selected
    time-gap setting (`FOLLOW_TIME_GAP_S`: close/medium/far =
    1.0/1.5/2.0s) times own speed, floored at
    `ACC_MIN_FOLLOW_DISTANCE_M` (3.0m); derives the lead vehicle's actual
    speed from own_speed + relative_speed; returns `min(driver_set_speed,
    lead_speed + ACC_GAP_ERROR_GAIN * gap_error)` — matches the lead
    vehicle's speed while correcting the gap, never commands faster than
    the driver's own cruise setting. This target speed feeds straight into
    the EXISTING `CruiseController.control()` throttle/brake law
    unchanged — no new pedal-control code, just a smarter target-speed
    input.
  - `LaneCamera` is the same externally-driven pattern for lane state
    (`set_lane_state(detected, lateral_offset_m, heading_error_rad)`) — no
    real lane geometry exists in this project to derive these from.
  - `LaneKeepingAssist.corrective_steering_deg(camera, manual_steer_deg,
    turn_signal_active)`: returns 0 if disabled, no lane detected, the
    turn signal is active (driver signaling an intentional lane change,
    read from `Lighting.indicator`), or manual steering already exceeds
    `LKA_DRIVER_OVERRIDE_DEG` (45°, treated as a deliberate driver
    override, same as how a real Pilot Assist won't fight actual steering
    input); otherwise a small proportional correction
    (`LKA_LATERAL_GAIN_DEG_PER_M` × lateral offset +
    `LKA_HEADING_GAIN_DEG_PER_RAD` × heading error, negated to steer back
    toward center), clamped to ±`LKA_MAX_CORRECTIVE_DEG` (12°). This
    correction is ADDED to the driver's manual steering command, never
    overrides it outright the way Park Assist Pilot does during a parking
    maneuver. Verified in isolated unit tests: no lane → 0 correction;
    0.3m rightward drift → -2.4° (correctly steers left/back toward
    center); turn signal active → suppressed to 0; large manual input →
    suppressed to 0; large drift → saturates at the -12° cap.
  - `Simulation` composes both: the cruise-control branch's `target_mps`
    now comes from `adaptive_cruise.effective_target_speed_mps(...)`
    instead of the plain set-speed; the LKA correction is added to the
    driver's manual steering angle before `steering.set_wheel_angle_deg()`
    (in the steering-resolution else-branch not covered by Park Assist
    Pilot). New `Simulation` methods: `set_lead_vehicle()`,
    `clear_lead_vehicle()`, `set_acc_follow_gap()`, `set_lane_state()`,
    `set_lane_keeping_assist_enabled()`. New telemetry:
    `acc_lead_vehicle_detected`, `acc_follow_gap_setting`, `lka_enabled`,
    `lka_lane_detected`.
  - Verified: with no radar target set, cruise control behaves identically
    to before (falls through to plain set-speed tracking) — confirmed no
    regression. With a synthetic lead vehicle inserted (40m ahead,
    closing), ACC correctly computed a target speed well below the cruise
    set speed and the car decelerated toward it (confirmed via direct
    computation: own_speed 41.4 m/s → target 33.1 m/s given the inserted
    lead vehicle, and observed deceleration over the following 20s of sim
    time).
  - ASSUMPTION throughout: exact factory tuning (radar range, time-gap
    steps, steering-assist gain/limit) isn't published for this car;
    plausible values for this class of system.
- **CAN bus + ECU layer**: 6 ECUs (engine, transmission, chassis, AWD, body, cabin) read
  live sim state and broadcast it as real byte-packed CAN frames (scale/
  offset encode-decode, not a plain dict dump) on realistic schedules
  (20-100 Hz). This part is purely observational — physics is unaffected
  whether or not anything subscribes to the bus. Message IDs/signal layouts
  are our own invented, plausible-looking set; Volvo's real DBC is
  proprietary and unpublished (confirmed via search — no official or
  open-source XC90 CAN layout exists anywhere).
- **DSTC intervention (traction control + ABS + ESC)**: unlike the ECUs
  above, `xc90_sim/dsc/` genuinely acts on the vehicle, not just observes
  it. `TractionControl` senses wheel slip over the CAN bus and cuts engine
  torque via `Engine.set_traction_control_limit()` when a driven wheel spins
  beyond threshold; `ABS` releases/reapplies each wheel's brake torque on
  detected lockup; `ESC` compares actual yaw rate to a kinematic reference
  (from steering angle + speed) and brakes a single wheel — inside-rear for
  understeer, outside-front for oversteer, the standard real strategy —
  additively, unlike ABS, since ESC can brake a wheel the driver never
  touched at all. Validated: under normal dry-road (mu=0.9) braking, ABS
  correctly stays inactive (brakes already grip-matched, never approach
  lockup); forcing a low-grip scenario (mu=0.25, ice) makes ABS engage and
  visibly pulse as designed; a moderate hard-cornering test showed ESC
  cutting the average yaw-rate tracking error from 44.4°/s down to 12.8°/s
  (~3.5x better) vs. the same maneuver with ESC disabled. Adding TCS brought
  the launch simulation's 0-60 from 4.44s down to **5.38s — matching this
  exact trim's published ~5.4s estimate almost exactly** (see "Vehicle
  identity" note above for the mass/tire correction that also fed into
  this number).
- **Sensor realism**: wheel speed is no longer the physics engine's exact
  omega — `WheelSpeedSensor` quantizes it to whole reluctor-ring pulses per
  10ms sample window (48 pulses/rev, ASSUMPTION) plus small Gaussian noise,
  which is why real wheel-speed sensors are imprecise at low speed (few
  pulses occur in a short window). The "vehicle reference speed" TCS/ABS/ESC
  all key off is now the **median of the 4 sensed wheel speeds** — a real
  "select" technique robust to any single wheel spinning or locking — not
  ground-truth body speed. One side effect: the sim is no longer bit-for-bit
  deterministic run-to-run (unseeded sensor noise), matching how real
  hardware behaves.
- **Trip logger**: a CAN-bus datalogger (same idea as real python-can/
  cantools tooling) that subscribes to the bus and produces a usage report
  for a full drive — % time per gear, per rpm band, per throttle band,
  converter-locked %, AWD front/rear split, brake-active %, peak g's.
- **Live routing**: point A/B can now be two real addresses, not just
  (distance, style). `trip/live_routing.py` geocodes both via Nominatim,
  fetches a real route via the OSRM public demo server (turn-by-turn steps
  + geometry, no API key), and queries Overpass for real traffic-signal/
  stop-sign node locations along it — then builds the drive cycle directly
  from the actual road: real per-segment distances/speeds, real turns
  (with a slowdown at each), and a real stop (decelerate/dwell/accelerate)
  at every traffic control matched to the route. This is a genuinely
  different, more accurate cycle than the synthetic (distance, style)
  generator, not just real distance fed into the same generic blocks.
  Two real bugs surfaced and were fixed while validating this against the
  route's own real distance (see "Bugs found and fixed" #10 and #11):
  transition/stop maneuvers were adding distance on top of the route's
  real distance instead of counting toward it, and OSM tags multiple
  signal-pole nodes per intersection, which was counting one real
  intersection as several separate stops. After both fixes, a real 10.2 km
  downtown-SF test route (Golden Gate Bridge to the Ferry Building) drove
  10.5 km (2% over) with 42 real stops in 25.6 min — vs. OSRM's naive
  14.8 min free-flow estimate, which doesn't model stopping at all.
  Overpass failures degrade gracefully (falls back to the segment-only
  cycle with a warning) rather than crashing the trip, since it's a shared
  public service that can time out or rate-limit.
  HTTP calls go through `curl` via `subprocess` rather than `urllib`/
  `requests` directly — diagnosed, not guessed: this machine's Python
  `ssl` module is linked against LibreSSL 2.8.3 (~2018-era, macOS system
  Python) and fails to TLS-handshake with router.project-osrm.org, and
  this affects `urllib.request` and `requests`/urllib3 identically (both
  share the same underlying `ssl` module) — confirmed by testing all three
  directly. `curl` succeeds because macOS links it against a different,
  current TLS stack.
- **Wear/degradation model**: `Simulation()` now defaults to modeling this
  car in its *actual current condition* (115,367 mi as of this car's latest
  CARFAX reading), not showroom-new. `wear/wear_model.py`'s `WearModel` is
  generic — for each wearable component (tires, front brakes, rear brakes,
  general engine condition, suspension bushings), it finds that
  component's most recent "replaced" event in `specs/service_history.py`
  (real CARFAX dates/mileages), and linearly degrades a condition fraction
  from 1.0 at that event toward an ASSUMPTION floor over an ASSUMPTION
  typical service life. To reflect a new real repair, just append one
  `ServiceEvent` to `service_history.py` — nothing else changes. At the
  car's real current mileage this gives: tires 75% (55,507 mi since last
  replacement — genuinely overdue), front brakes 85.7% (32,151 mi since),
  rear brakes 95.4% (10,346 mi since, replaced most recently), engine 97.4%
  (mild wear at 115k total miles), bushings 92.3% (never replaced, aging
  with the whole car). These feed real physics hooks: `TireModel.grip_scale`,
  `Brakes.front_pad_condition`/`rear_pad_condition`, `Engine.condition`
  (torque output), `RideModel`'s damper coefficients (bushing softening).
  `Simulation(mileage=0)` gives the showroom-new baseline for comparison.
  Validated: at the real (worn) mileage, cornering at the same 90° steering
  input now correctly tops out at a lower lateral g (0.61g vs ~0.8g fresh)
  with less roll (3.0° vs ~4-5°) — a worn-tire car reaching its lower grip
  limit sooner, exactly as expected. One genuinely interesting and
  counterintuitive result: the worn car's 0-60 (5.18s) was *faster* than
  fresh (5.38-5.51s across repeated runs, confirmed outside the sensor-
  noise band) — plausible, not a bug: slightly less torque *and* less grip
  together mean less wheelspin overshoot past the tire's peak-slip point
  during launch, so TCS manages the launch more cleanly. A real-world
  echo of why more power doesn't always mean a quicker launch once
  traction, not engine output, is the limiting factor.
- **Real-data calibration pass**: researched every remaining ASSUMPTION
  constant against published instrumented-test data rather than more
  guessing. Found genuinely useful reference numbers from Car and Driver's
  test of a 2016 XC90 T6 AWD **Inscription** (a different, heavier trim
  than this Momentum car — flagged, not glossed over): 0.81g skidpad,
  161 ft 70-0mph braking, 5.8s 0-60. Used the skidpad figure to calibrate
  `TIRE_FRICTION_COEFFICIENT` (0.90 → 0.82) after building a proper peak-
  cornering sweep test (a moderate single-steering-angle sample isn't the
  same measurement as an actual skidpad's full-lock sweep) — this sim's
  own peak sustained lateral g now reads 0.808g, matching real to within
  0.2%. `MAX_BRAKE_DECEL_G` was left at 1.0 after confirming it already
  implies almost exactly the real car's ~1.0g average braking deceleration
  (the sim's own 70-0 stop distance is 186 ft, 16% longer than real —
  most likely ABS's conservative release fraction, not the peak-g
  assumption, since that's what actually limits realized stopping
  distance versus tire capability). A wheel-size conflict between two
  searches (235/60R18 vs 235/55R19) turned out to matter little for physics
  either way (<0.3% rolling-radius difference) but was resolved anyway —
  the owner confirmed this car actually has the 19" wheels.
- **Second calibration round — weight distribution + AWD engagement
  behavior**: found real published weight distribution (52/48 front/rear,
  from a detailed technical review comparing it directly to the Mercedes
  GL/GLE) and corrected `FRONT_WEIGHT_FRACTION` from an 0.55 guess.
  Combined with the tire mu correction above, this pushed the sim's 0-60
  out to 6.2s — a more rear-biased split gives a front-biased AWD system
  less front grip to launch on, which is real physics, not a bug, but it
  prompted checking whether a real feature was missing rather than just
  accepting the number. It was: Haldex Gen 3+ (this car's Gen 5 included)
  is documented as *proactive* — it pre-tensions the clutch toward the
  rear based on anticipated demand (throttle position at low speed), not
  only reactively after slip has already developed. `HaldexAWD.split()`
  only had the reactive half; added the proactive half (`specs/awd.py`,
  `PROACTIVE_SPEED_THRESHOLD_MPS`), taking whichever of the two calls for
  more rear engagement at a given instant. Also recalibrated
  `TCS_SLIP_THRESHOLD` to this tire model's own measured peak-grip slip
  ratio (0.18, sampled directly from `TireModel.forces()`) instead of an
  earlier value that cut in before the tire reached its own maximum, and
  raised `TCS_MIN_TORQUE_FRACTION` (0.15 → 0.35) since real production TCS
  calibration prioritizes forward progress over eliminating slip entirely.
  Net result: 6.12s — slower than the earlier ~5.4s figure, but now
  converging toward the one number from an actual rigorous instrumented
  test (C&D's 5.8s Inscription, a heavier trim) rather than an unverified
  Momentum-specific estimate from a less rigorous source. Documented
  honestly rather than further tuned to hit a specific number — real
  variance between test conditions, drivers, and this specific car's
  actual tires means an exact match was never really achievable, and
  chasing one past this point would mean fitting parameters to a target
  instead of to evidence.
- **Live OBD2 integration**: `xc90_sim/obd/` bridges a real car's OBD2 port
  onto the exact same `CANBus` and message formats the simulated ECUs
  publish, so `TripLogger` runs completely unchanged on real data — this
  was the user's stated ultimate goal for this whole project. Genuinely
  available from generic (non-manufacturer-specific) OBD2: engine RPM,
  throttle position, calculated load, vehicle speed. Two things aren't
  directly available but are legitimately derived rather than faked: gear
  (estimated from the RPM/wheel-speed ratio matched against this project's
  own real TG-81SC gear ratios) and longitudinal acceleration (the numerical
  derivative of consecutive real speed readings, clamped to a physically
  sane range after a mocked-connection test caught it spiking to 32.7g on
  a too-short polling interval — a real risk with ELM327 response-time
  jitter, not just a test artifact). Lateral accel, yaw rate, steering
  angle, brake pedal %, and AWD torque split are NOT available from generic
  OBD2 at all (would need Volvo's proprietary extended PIDs, which aren't
  publicly documented) — TripLogger's stats for these will honestly show
  no data rather than a guessed number. **Untested against real hardware**:
  written and reviewed against python-OBD's documented API (confirmed it
  supports both USB and WiFi ELM327 adapters through the same connection
  string, via pyserial's `socket://` URL scheme) and validated at the logic
  level with a mocked connection, but there was no physical adapter or car
  available to verify timing, PID availability, or connection behavior
  against — expect to need to debug the actual port/IP for your specific
  adapter (`examples/run_obd_trip.py` has troubleshooting notes).

## Validated behavior

- 0-60 mph: 6.12s, 1/4 mile: 14.6s @ 101.0mph. Real reference points:
  Car and Driver's instrumented test of the heavier Inscription trim:
  5.8s / 14.6s @ 97mph, 0.81g skidpad, 161ft 70-0mph braking — see "Bugs
  found and fixed" and the calibration entries above for how this number
  was arrived at (not fitted to match it exactly).
- Idle creep settles at ~3.7 mph with throttle/brake off, matching real
  torque-converter-car behavior (not hard-coded — it emerged from the model).
- Hard braking shows correct nose-dive pitch (opposite sign from
  acceleration squat), decelerates cleanly to a stop.
- Manual (Geartronic) mode holds a requested gear indefinitely, ignoring the
  adaptive auto-shift map, while still protecting against over-rev/stall.
- Sustained cornering settles into a stable, repeating circular path with
  realistic lateral g (~0.8g) and roll angle (~4.0°) — no divergence.
- A 15 km "mixed" trip produces a plausible usage report (12% 1st/7th-gear-
  heavy for the city portions, ~50% in 7th overall, 93% converter-locked,
  ~52% avg Haldex front bias); city-only and highway-only trips at 5 km/20 km
  produce visibly distinct, sensible profiles (city: gears 1-4 only, 55% in
  4th; highway: 95.5% in 7th).

## Bugs found and fixed along the way

These were real defects caught by testing against expected physical
behavior, not just style issues:

1. **Shift logic used slip-corrupted wheel speed.** Using driven-wheel speed
   as a stand-in for transmission input speed meant launch wheelspin could
   spike the apparent rpm and trigger a spurious upshift. Fixed by using an
   idealized (no-slip, vehicle-speed-derived) signal for shift *decisions*,
   matching why real TCUs key off a VSS rather than the driven wheel's own
   sensor.
2. **Torque converter lockup used the same slip-corrupted signal**, so
   wheelspin could falsely trigger lockup and rigidly slave the engine to a
   freely-spinning wheel — a self-reinforcing runaway. Fixed by splitting
   the converter's *physical* speed ratio (real wheel speed, used by the
   fluid-coupling physics) from its *control* speed ratio (idealized speed,
   used only for the lockup decision).
3. **Naive instantaneous slip computation was numerically unstable** against
   the saturating tire curve's peak-then-falloff shape — a known issue in
   tire simulation. Fixed with a **slip relaxation length**: real tires take
   a few tenths of a meter of rolling distance for the contact patch to
   build up slip, so this is a physically real effect, not just a numerical
   patch.
4. **Pitch/roll restoring-moment equations had a sign error** (positive
   instead of negative feedback), confirmed by hand-linearizing the
   equations — the coefficient of `theta`/`phi` came out `+k` instead of
   `-k`. Caught because a standalone rigid-body test diverged instead of
   settling.
5. **Small residual static-pitch bias** from reusing whole-vehicle
   CG-to-axle distances for the sprung-mass-only rigid body (unsprung mass
   subtraction slightly shifts the sprung mass's own front/rear split).
   Fixed by deriving separate sprung-mass-specific arms.
6. **Conflated state-derivative with felt acceleration.** `vx_dot`/`vy_dot`
   (used to integrate velocity) include rotational cross-terms
   (`Fx/m + vy*r`, `Fy/m - vx*r`); the accelerometer-felt acceleration that
   should drive suspension squat/dive/roll and telemetry is just `Fx/m`,
   `Fy/m` — no cross-terms. Conflating them made lateral-g telemetry read
   near-zero during a perfectly steady, obviously-cornering circle.
7. **Trip driver model instantly floored the throttle at every stop-light
   launch** (proportional control on a large initial speed error saturates
   immediately), making every city-cycle launch look like a full-throttle
   drag-strip start and skewing the usage stats toward unrealistic slip
   events. Fixed with a pedal rate limiter (mimics a human easing into the
   throttle); peak accel now settles near the tire's real ~0.9g grip ceiling
   instead of an artificial instant-full-throttle spike.
8. **Anti-roll bar stiffness constants were defined but never wired into
   the roll equation** — `FRONT_ARB_ROLL_STIFFNESS_NM_PER_RAD` and
   `REAR_ARB_ROLL_STIFFNESS_NM_PER_RAD` existed in specs (and the ride
   model's own docstring claimed "front-biased anti-roll distribution")
   but `phi_ddot` never referenced them. Caught because a steady circular
   turn, freshly re-tested after the per-wheel refactor exposed genuine
   per-corner loads to the tire model, showed a real ~2s-period roll/yaw
   oscillation instead of settling — traced to roll reaching ~7° and
   pushing the outer corner's compression past its bump-stop travel limit
   (0.09 m), triggering a hard 12x stiffness discontinuity every cycle.
   Wiring in the ARBs as a direct torsional spring on `phi` stiffened the
   roll response enough to stay clear of the bump stop; the turn now
   settles to a constant ~4.9° roll with no oscillation.
9. **Roll-center construction used the wrong contact patch.** The standard
   method draws a line from a wheel's front-view instant center to the
   *opposite* wheel's contact patch; using the *same*-side contact patch
   instead (an easy mistake — the two look similar on paper) crosses the
   centerline almost all the way across the car rather than roughly in the
   middle, making the computed roll-center height wildly oversensitive to
   small hardpoint changes (swung from -2,729mm to +2,396mm for a small IC
   shift during tuning, before the fix). Caught by iterating hardpoints
   toward realistic targets and noticing the results couldn't be made
   stable — fixed by using the correct opposite-side construction, after
   which sensible hardpoint coordinates gave sensible, stable results
   directly.
10. **Live-routing drive cycles added distance on top of the real route
    instead of accounting for it.** Both the per-step turn/ramp transitions
    and the inserted traffic-control stops modeled the vehicle covering
    "extra" distance while decelerating/accelerating, on top of — not as
    part of — the step's real distance budget. Caught by integrating the
    built cycle's own target-speed profile and comparing it against the
    route's real OSRM distance: a 10.2 km test route came out to 17.2 km of
    theoretical distance, 69% too much. Fixed by tracking distance as the
    primary invariant in both `_build_segments_from_steps` and
    `_splice_in_stops` — a stop or transition's own coast/accelerate
    distance now counts toward the segment's remaining real distance,
    exactly like it costs a real driver time but not extra road. Final
    result: 2% over real distance, not 69%.
11. **Traffic-signal counting treated one intersection as several.** OSM
    tags traffic signals per physical pole (often one per approach), not
    one node per intersection, so a real 4-way stoplight can appear as 3-4
    separate `traffic_signals` nodes a few meters apart. Matching each to
    the route independently counted 106 "stops" on a 10.2 km route — about
    one every 96 m, obviously wrong. Caught by inspecting the gaps between
    matched control points (median 11.7 m, many at exactly 0 m — the tell
    that they were the same intersection). Fixed by deduplicating any two
    matches within 40 m of each other, bringing the count down to a
    plausible 42.
12. **Car never fully stopped under hard braking.** At very low true speed,
    the wheel-speed sensor's pulse quantization (see "Sensor realism")
    floors the *reference* speed reading to exactly 0 kph while individual
    wheels still read small nonzero values — `(wheel - ref)/ref` with
    `ref` floored to a 1 kph minimum then reads as ~50% "slip," which looks
    exactly like lockup to ABS and releases the front brakes to 15%
    indefinitely. Result: the car converged to a persistent ~0.13 m/s
    creep under full brake pedal instead of reaching zero — caught because
    a 70-0 mph braking-distance test never terminated. Real ABS avoids this
    exact regime by disabling itself below a minimum speed, since wheel-
    speed sensing genuinely is unreliable there and there's no stopping-
    distance benefit to modulating brake pressure when you're basically
    already stopped — added the same guard (`ABS_MIN_SPEED_KPH = 5.0`).
    TCS has an analogous but less severe version of the same issue (its
    reference-speed floor was raised from 1 to 8 kph rather than disabled
    outright, since TCS has to keep working from a dead stop).
13. **Reverse driving exposed a latent brake-torque wheel-lockup bug.**
    Adding a real PRND gear selector (see "What's implemented") required
    removing two forward-only clamps (`vx_mps` and wheel `omega` were both
    hard-floored at 0) that, it turned out, had been silently absorbing a
    real defect in the brake model the whole time: once commanded brake
    torque exceeds what the (now-saturated) tire's reaction can resist —
    routine at very low speed, exactly where ABS is intentionally disabled
    (see bug #12) — nothing stopped the excess torque from spinning the
    wheel up in the *opposite* rotational direction indefinitely, since a
    dissipative friction torque was being integrated exactly like a motive
    one. Caught by testing a reverse-then-brake-to-a-stop maneuver: instead
    of settling, speed oscillated indefinitely between roughly +2 and -3 mph
    while one front wheel's omega ran away to 250+ rad/s. Real friction
    brakes can only ever remove rotational energy, never add it in a new
    direction — fixed in two parts: (a) `Wheel.step()` now takes drive and
    brake torque as separate arguments (previously pre-summed) and clamps
    omega to exactly 0 — and holds it there on every subsequent tick, not
    just the first — whenever brake torque would otherwise flip its sign;
    (b) `Brakes.axle_torques_nm()` now also caps commanded deceleration at
    whatever brings the car to an exact stop within the current tick
    (dt-aware), so the vehicle-body level doesn't overshoot either. Forward
    braking-to-a-stop was re-verified unaffected (0-60/quarter-mile times
    identical before and after); a small residual settling wobble remains
    (sub-1 mph, decaying within ~2s) — same category of tolerated small
    residual as bug #12's remaining creep, not a new pathological failure.
14. **Radiator sizing was a bare guess that let coolant temperature run
    away unbounded under sustained load.** `RADIATOR_MAX_DISSIPATION_W`
    was initially set to 25000 (25kW) as a first-pass ASSUMPTION —
    plausible-sounding in isolation, but never checked against what this
    engine's own combustion model actually produces. Testing a sustained
    ~100mph/half-throttle highway cruise (added specifically to exercise
    the new cooling system under sustained load, not just a launch)
    showed the sim's own real fuel-flow output sends ~67.6kW to the
    coolant at that condition (measured directly from the sim's real fuel
    burn rate, not assumed), and full-throttle near redline sends
    ~180kW — so a 25kW-rated radiator meant coolant temperature ran away
    unbounded (over 300°C within a few minutes) under any sustained load
    at all, which is unrealistic (real cars don't overheat cruising at
    highway speed). Fixed by raising `RADIATOR_MAX_DISSIPATION_W` to 90000
    (90kW), sized directly against the sim's own fuel-flow output rather
    than an independently published spec (none exists for this exact
    car — still flagged ASSUMPTION, just a checked one now instead of a
    bare guess). Verified after the fix: coolant settles into the correct
    thermostat-regulated equilibrium (~87-90°C, cycling the thermostat
    open/closed around `THERMOSTAT_OPEN_TEMP_C`) under the same sustained
    highway-cruise test, instead of runaway heating.
15. **Propshaft torsional stiffness was a bare guess that produced ~40° of
    windup at peak torque — implausible for a real steel shaft.**
    `TORSIONAL_STIFFNESS_NM_PER_RAD` had been 8000 Nm/rad since `Propshaft`
    was first introduced telemetry-only (see "What's implemented" ->
    "Drivetrain hardware reification"); because that value never fed back
    into the torque path, an unrealistic number had no visible
    consequence and went unchecked against a plausible real shaft
    geometry. It surfaced only when closing the windup loop into the real
    torque path was attempted (2026-09-01) and the resulting windup angle
    was computed for the first time at this car's peak simulated
    rear-axle torque during a hard launch: ~40°, an order of magnitude
    beyond what a real propshaft (a few degrees at most, even at peak
    torque) would ever see — closing the loop on that value would have
    distorted the whole rear torque path with an unrealistically soft
    spring. Caught and fixed *before* closing the loop, not after. Fixed
    by re-deriving the constant from first principles (`k = G*J/L`) for a
    plausible tubular propshaft (steel, G=79 GPa, ~70mm OD/64mm ID, ~1.5m
    length): computed k≈37,000 Nm/rad, rounded to 40,000 Nm/rad. Verified:
    max windup during the same hard-launch test dropped from ~40° (bug)
    to ~8.3° (fixed) — a defensible range for this class of shaft — before
    the loop was closed; the regression suite (0-60, 1/4 mile) was
    unaffected either way, since telemetry-only windup couldn't move it,
    confirming the bug had zero visible symptom until the loop-closing
    work exposed it.

## Left to do

- **Scope boundaries that emerged from building the five whole-car-audit
  systems (2026-08-24)** — cooling, exhaust/turbo/O2/EGR, drivetrain
  hardware, airbags/SRS, and radar-based ADAS are all built now (see
  "What's implemented"), but building them surfaced their own honest
  edges. Six of the seven originally tracked here were closed in the
  2026-09-01 pass (propshaft windup closed into the torque loop, real
  water pump/coolant-flow model, transmission cooler reified,
  Occupant Classification System child-seat detection, SRS self-test/
  bulb-check diagnostics, and a second EGR dilution mechanism — see
  "What's implemented" for each) — removed from this list since they're
  no longer gaps. Two remain, for different reasons:
  - **Airbags have no real collision/contact physics to trigger them** —
    this sim has no obstacles to actually crash into, so deployment keys
    off a single instantaneous-g threshold against the real body-frame
    accelerometer rather than a real crash-pulse-shape-integrating
    algorithm (proprietary on a real car, and there's no crash pulse here
    to integrate anyway). Not attempted this pass; closing it for real
    would mean building actual collision/contact physics (obstacles,
    penetration depth, crash-pulse shape over tens of milliseconds), a
    substantially different kind of project than vehicle dynamics — flagged
    here for visibility, not scheduled.
  - **ACC/LKA sensors are externally-driven virtual sensors, not derived
    from real traffic or lane geometry** — `ForwardRadar` and `LaneCamera`
    have their readings set from outside (`set_lead_vehicle()`,
    `set_lane_state()`), the same pattern already used for
    `BlindSpotMonitor`/`ParkingAssist`, since this project has no actual
    traffic simulation (other vehicles with real positions) or lane
    geometry to derive these from directly. **Deliberately NOT attempted
    in the 2026-09-01 pass, and not a deferred TODO** — this is a
    permanent scope boundary, considered and declined on purpose, not a
    bounded closable gap that just hasn't been gotten to yet. Building
    real traffic/lane geometry would mean building an actual environment/
    traffic simulator: other vehicles with real positions and motion, real
    road/lane curvature to derive lateral offset and heading error from —
    a fundamentally different kind of project than vehicle dynamics
    simulation, not an extension of it. The existing externally-driven
    virtual-sensor pattern (matching `BlindSpotMonitor`/`ParkingAssist`,
    which take obstacle/gap state from outside for the same reason) is the
    correct, honest design for a project scoped to the vehicle itself —
    not a failure to close a gap, a deliberate boundary that should stay
    documented as such.
- **Verify the OBD2 bridge against real hardware** — built and validated at
  the logic level (see "What's implemented"), but never run against an
  actual ELM327 adapter or car. Needs the user's own USB/WiFi adapter to
  confirm connection behavior, PID availability, and real-world polling
  timing.
- **Vehicle software features** — fuel *chemistry/aging* specifically
  (octane rating effects, ethanol content, fuel going stale over long
  storage — the fuel *tank* itself, with real consumption/capacity/low-
  fuel warning, is now built, see "What's implemented"), real GPS/nav
  hardware (live map position — `Infotainment` only has a destination/
  distance/ETA pass-through, not an actual position fix). Explicitly in
  scope as future software-feature additions, not permanently excluded as
  "not physics-relevant" — just not built yet. (Everything else originally
  in this bucket — body closures, cabin electronics, lighting circuits,
  windows, mirrors, blind-spot monitor, PRND gear selector + real reverse
  driving — is now built; see "What's implemented.")
- **Reverse vehicle dynamics is functional but not independently
  hardened**: forward driving (the vast majority of this project's testing)
  is unaffected, and a reverse-then-brake-to-a-stop maneuver was explicitly
  tested and converges correctly (see bug #13). But things like reverse
  steering feel (the slip-angle formula doesn't re-derive sign behavior
  for negative vx) and reverse-specific ESC/TCS tuning haven't been
  separately validated the way forward driving has — reverse is meant for
  low-speed parking maneuvers, not verified at any real speed or under
  cornering.
- **Park Assist Pilot's honest limitations** (see "What's implemented" for
  what it does do): fixed-angle two-phase geometry, not a true continuously
  -optimized path — a real spot that's unusually tight or oddly shaped
  could need more than the two phases modeled here. Parallel parking only
  (no perpendicular/bay parking geometry). Gap-scanning uses a single
  side-distance reading, not a full sensor-fusion map of the space. "Park
  out" (pulling back out of a spot using the pilot) isn't built, only the
  "park in" (scan + reverse-in) direction.
- **Full 4-bar upright solve** — camber/roll-center/anti-dive/squat now come
  from real 3D hardpoints via the instant-center/swing-arm method (see
  "What's implemented"), which is the standard *simplified* K&C hand-
  calculation technique, not a full nonlinear 4-bar linkage position solve
  (upper arm, lower arm, and upright as three rigid bodies with 2 DOF solved
  simultaneously). The swing-arm method is accurate for small-to-moderate
  travel (our ±90mm bump/droop) but diverges from the exact solve at larger
  travel or more radical linkage geometries.
- **Manufacturer tire data** — still generic Pacejka textbook shape factors.
  Volvo's OEM data is proprietary/unpublished. Michelin sells real datasets
  (paid, €5k-€25k) and offers a free sample via a request form, but
  submitting it needs the user's own identity info and hasn't been done yet.
- **Wear model refinements** — the current model is a single linear
  condition-fraction per component; it doesn't yet cover engine mounts,
  battery/12V electrical condition, or account for the 2021 accident's
  possible (unknowable without inspection) alignment/structural effects.
- **Sensor-fusion reference speed** — TCS/ABS/ESC use a median-of-4-wheels
  "select" estimate (see "What's implemented"), not the full accelerometer-
  fused estimate real systems use to bridge gaps between wheel-speed samples.
- **Traffic signal timing/phase** — a matched signal always costs a flat
  expected delay (`SIGNAL_EXPECTED_DELAY_S`); no modeling of the real
  chance of catching it green, or of actual signal cycle length.
- **Real-time traffic conditions** — OSRM's routing profile is a free-flow
  time estimate; no live congestion data (would need a paid traffic API).
- **Driver interface / telemetry dashboard** — no live gauges or interactive
  control yet, only scripts.

## Known tuning gaps

- 0-60 is now 6.12s, slower than an earlier ~5.4s figure — see "Bugs found
  and fixed" and the real-data calibration entries for the full story
  (corrected weight distribution + tire mu + a real proactive-Haldex
  feature this uncovered was missing). This is now anchored to a real
  instrumented test (C&D's 5.8s Inscription) rather than an unverified
  Momentum-specific estimate, but the gap (a lighter Momentum reading
  slower than a heavier Inscription) suggests either this car's real
  tires grip less than the Inscription's tested tires, or the TCS/Haldex
  calibration is still more conservative than a real production tune —
  not fully resolved, flagged honestly rather than tuned away.
- Roll angle at the limit (~3.6° at ~0.74g) is a reasonable, physically-
  derived number now that anti-roll bars are wired in (bug #8) and roll
  center height comes from real linkage geometry — but the ARB stiffness
  and hardpoint coordinates themselves remain unvalidated assumptions,
  since no public data exists to check them against.
- `BASE_FRONT_BIAS = 0.90` (Haldex Gen5 no-slip front bias) checked against
  forums per owner request (2026-08-18): a 2005 Volvo PR release (real
  primary-source quote, found via SwedeSpeed) states the *predecessor*
  Gen2/3/4 coupling ran 95/5 front-biased at rest, up to 95% transferable to
  the rear under slip — same order of magnitude as the 0.90 already coded,
  but for older hardware in different-platform cars, not this car's Gen5/SPA
  system, so not adopted as an exact replacement. Three other specific
  numbers surfaced (100/0 until slip, 70/30 stock, 50/50 fully clamped) were
  only AI-summarized forum claims with no traceable primary source (threads
  paywalled/bot-blocked on fetch) and were discarded as unreliable rather
  than used. Also resolved a naming worry: "BorgWarner" (industry press) and
  "Haldex Gen5" (enthusiast/parts naming) are the same hardware — BorgWarner
  bought Haldex Traction Systems in 2013 — so no renaming was needed.
  Net: 0.90 stays flagged ASSUMPTION, now corroborated in shape rather than
  a bare guess. See `xc90_sim/specs/awd.py` for the full citation.
- **Broader assumption-audit research pass (2026-08-19)**, checking the
  remaining ~10 highest-value ASSUMPTION-flagged constants against real
  published/forum data (manufacturer specs, NHTSA, SAE, parts catalogs,
  forums) — one confirmed naming error fixed, a few numbers tightened, most
  stayed unverified (see each spec module's own comment for full citations):
  - **Fixed a real naming error**: this project called the transmission
    "AW8G30" throughout — no evidence that designation exists. It's actually
    the Aisin **TG-81SC** (marketed as AWF8F45; also EAT8/GA8F22AW/AF50-8/
    AQ450 at other OEMs), confirmed via OEM parts listings, SwedeSpeed, and
    cross-reference catalogs. Renamed in all comments/docstrings (`specs/
    transmission.py`, `powertrain/transmission.py` (now
    `transmission/transmission.py`), `obd/bridge.py`,
    `STATUS.md`) — gear ratios themselves weren't touched, since they were
    already treated as sourced from a real Volvo spec sheet (not flagged
    ASSUMPTION), and a different OEM's application of the same shared
    transmission has a different ratio spread by design, so it isn't
    evidence these particular ratios are wrong.
  - **Corrected the rear suspension architecture**: it's not a steel coil
    spring. Volvo's own press material confirms the standard (non-Four-C)
    rear uses a transverse composite leaf spring; only the front is a coil
    strut. The sim's linear-spring-rate model still applies fine physically
    (a leaf spring's vertical rate is linear near ride height, same as a
    coil) — no equation changes needed, just the corrected description in
    `specs/suspension.py`.
  - **Tightened rolling resistance**: `0.011` was inconsistent with every
    plausible OEM tire candidate found (EU tire-label data puts real
    touring-tire candidates in Class B/C, while 0.011 sits at/above the
    worst class, E) — lowered to `0.0085`, still flagged ASSUMPTION pending
    an exact-size (235/55R19) label fiche.
  - **Confirmed** (already-coded values now backed by real citations, no
    change needed): ABS reluctor tooth count (48 — matches a genuine Volvo
    part number); brake front-bias direction (real 336mm front / 320mm rear
    OEM rotor sizes support front-biased, though not the exact 65/35 split).
  - **Researched but still unverified** (real search effort spent, no
    reliable data recovered — stays an honest guess, not silently dropped):
    CG height (a promising NHTSA rollover-rating lead didn't pan out — the
    raw Static Stability Factor filing 403'd every fetch attempt), unsprung
    mass per corner, anti-roll bar stiffness (a real 22mm OEM rear bar
    diameter was found via IPD's spec table, but couldn't be safely
    converted to this sim's Nm/rad units without IPD's test-rig geometry),
    spring rates, suspension travel, torque-converter stall speed, crank
    inertia, and boost-lag time constant (though the supercharger/turbo RPM
    handoff points — idle-1600rpm supercharger, turbo spooling by ~3500rpm —
    are now reasonably corroborated across independent sources, even if the
    time-based tau isn't).
  - Not re-checked at all: Pacejka tire shape factors, slip relaxation
    lengths, shift-cooldown timer, driver-model control gains, drive-cycle
    constants — these are generic tire-physics/numerical-modeling choices,
    not facts about this specific car that any manufacturer or forum would
    ever publish, so re-searching them wouldn't produce anything more
    reliable than what's already there.

## How to run it

```
python3 examples/zero_to_sixty.py
python3 examples/run_trip.py 15 mixed      # distance_km, style: city|highway|mixed
python3 examples/run_real_trip.py "1600 Pennsylvania Ave, Washington DC" "Arlington National Cemetery"
```

Or drive it interactively from a script:

```python
from xc90_sim.sim import Simulation

sim = Simulation()
sim.set_driver_inputs(throttle=1.0, brake=0.0)
sim.set_steering_wheel_angle_deg(90)
# sim.set_transmission_mode('manual'); sim.request_upshift()
for _ in range(1000):
    sim.step(0.002)
print(sim.telemetry())
```

Or listen to the CAN bus directly, same as a real datalogger would:

```python
from xc90_sim.sim import Simulation
from xc90_sim.ecu.engine_ecu import ENGINE_DATA

sim = Simulation()
sim.can_bus.subscribe(ENGINE_DATA.arbitration_id, lambda f: print(f.message.decode(f.data)))
sim.set_driver_inputs(throttle=1.0, brake=0.0)
for _ in range(100):
    sim.step(0.002)
```
