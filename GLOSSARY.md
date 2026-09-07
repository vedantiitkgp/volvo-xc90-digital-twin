# Glossary

Plain-English explanations of every technical term used across `xc90_sim/`, organized by subsystem to match the codebase layout. Each entry says what the term means, and — where it's not obvious — why it matters to this specific simulation.

## Powertrain (`engine/`, `transmission/`, `drivetrain/`, `specs/engine.py`, `specs/transmission.py`)

**Twincharger** — an engine with both a turbocharger (exhaust-driven forced induction) and a supercharger (belt-driven forced induction) working together. The supercharger fills in low-rpm boost instantly (no exhaust flow needed yet), and the turbo takes over as rpm rises — this is why the Drive-E engine's torque curve is flat from 2200 rpm rather than ramping in gradually like a plain turbo would.

**Boost lag** — the delay between pressing the throttle and the engine actually delivering full torque, caused by the turbo needing exhaust flow to spool up. `engine.py`'s `BOOST_LAG_TAU_S` models this as a simple exponential lag on delivered torque.

**Calculated load** — an OBD-II term (PID 0x04) for "how much of the engine's available torque at this rpm is currently being used, as a fraction." `Engine.calculated_load_frac` mirrors this real diagnostic signal.

**Torque converter** — the fluid coupling between engine and transmission in an automatic gearbox (no clutch pedal). Has two sides:
- **Pump** — spun by the engine, flings transmission fluid outward.
- **Turbine** — connected to the transmission input shaft, catches that flung fluid and spins the gearbox.
- **Stator** — a stationary vaned wheel between pump and turbine that redirects fluid flow, which is *how* the converter multiplies torque at low speed ratios (not present as a separate object in this code, but its effect is baked into the torque-ratio curve).
- **Capacity factor** — how much torque the pump absorbs from the engine at a given speed, independent of what the engine "wants" to produce. This is what stops the engine from just free-revving against no load.
- **Torque ratio** — how much the turbine's output torque is multiplied versus the pump's input torque; highest at stall (SR=0), tapers to 1.0 as the two sides sync up.
- **Speed ratio (SR)** — turbine speed ÷ pump speed. 0 = fully stalled (car stationary, engine revving), 1.0 = pump and turbine spinning at the same speed.
- **Lockup clutch** — a mechanical clutch inside the converter that locks pump directly to turbine once SR is high enough, eliminating fluid-coupling slip (and the efficiency loss that comes with it) for cruising.
- **Stall speed** — the rpm the engine settles at when held stationary at full throttle (torque convertor absorbs everything the engine can produce, at that rpm).

**Geartronic** — Volvo's name for a manual tip-shift mode on an otherwise-automatic transmission: nudge the lever (or use paddles) to request a specific up/downshift, while the transmission still protects against over-revving or stalling.

**Open differential** — a gear mechanism that splits engine torque equally between two wheels on the same axle while letting them spin at different speeds (needed because the outer wheel in a turn travels a larger circle than the inner one). Its well-known downside: if one wheel loses all grip (ice, one wheel off the ground), it can spin freely while the other wheel — even with full grip — gets no more torque than the spinning one, because torque is split *equally*, not by need.

**Propshaft** — the driveshaft connecting the front and rear halves of an AWD driveline (through the Haldex clutch, in this car). "Propshaft slip" = front and rear ends of that shaft trying to turn at different speeds, which is what the Haldex system reacts to.

**Final drive ratio** — the fixed gear reduction between the transmission's output and the wheels (separate from the multi-speed gearbox ratios), part of every gear's overall reduction.

**Redline / fuel cut** — the maximum safe engine rpm; real ECUs cut fuel injection above it to prevent over-revving, which is why torque drops to zero at `REDLINE_RPM` in the torque curve.

## Cooling System (`cooling/cooling_system.py`, `specs/cooling.py`)

**Thermostat** — a wax-pellet valve that blocks coolant flow to the radiator while the engine's cold (so it warms up faster) and opens once it reaches a set temperature. Modeled here with 3°C of hysteresis (opens above one temperature, doesn't close again until a few degrees below it) to avoid rapidly cycling open/closed right at the threshold.

**Radiator** — the heat exchanger that rejects heat from the coolant to outside air; how much heat it can reject depends on airflow through it (road speed, or the electric fan when stationary), not just its own size.

**Coolant** — the fluid (water + antifreeze in a real car) that carries heat away from the engine block to the radiator. Its temperature here evolves from a real energy balance: a fraction of the engine's own fuel-chemical-energy output in, radiator + passive ambient rejection out.

**Water pump (electric coolant pump)** — the component that actually circulates coolant around the loop; this engine uses a genuine ELECTRIC pump (not the older belt-driven mechanical kind), which is why the ECU can vary flow independently of engine rpm — ramping it up under load, holding it near-zero during cold start so the engine warms up faster, and even keeping it running for a while after a hot shutdown ("heat soak" protection, so a turbocharger housing doesn't locally boil the coolant right around it after the pump that was cooling it stops). Radiator heat rejection here depends on both airflow (existing) and coolant flow rate (this pump) — starving either one limits how much heat actually gets rejected, same as a real car.

## Tires & Traction (`chassis/tire_model.py`, `chassis/wheel.py`, `specs/tire.py`)

**Slip ratio** — how much a tire's surface speed differs from the vehicle's actual ground speed, as a fraction. Positive = wheel spinning faster than the car is moving (under power); negative = wheel spinning slower (under braking, heading toward lockup). Zero slip doesn't mean "no grip" — a small amount of slip is *required* to generate any tire force at all; the question is how much.

**Slip angle** — the angle between the direction a tire is pointed and the direction it's actually traveling. This angle, not the steering angle itself, is what actually generates cornering (lateral) force.

**Magic Formula / Pacejka model** — the industry-standard mathematical shape (named after Hans Pacejka) for how tire force rises with slip, peaks, and then gently falls off — as opposed to a flat "never exceeds mu×N" cap. The `B`/`C`/`E` constants in `specs/tire.py` are its shape parameters (stiffness, shape, curvature).

**Friction ellipse (combined slip)** — the principle that a tire has one shared grip budget for braking/accelerating force *and* cornering force, not two independent ones — using some grip for cornering leaves less available for braking, and vice versa. Modeled here by scaling the combined (Fx, Fy) vector down if its length exceeds the available peak force.

**Relaxation length** — the small distance (a few tenths of a meter) a rolling tire needs to travel before its contact patch fully "catches up" to a sudden change in slip. Physically real (tire carcass flex), and also the fix for a numerical instability this project hit when slip was computed instantaneously against the Magic Formula's peak-then-falloff curve.

**Coulomb friction** — the simple textbook model "friction force = mu × normal force, full stop," with no dependency on slip amount. This project's first-pass tire model used this before being replaced by the Magic Formula; it's mentioned in code comments as the "flat cap" being deliberately avoided.

**Rolling resistance** — the small constant retarding force from tire deformation as it rolls, even with zero slip and zero braking — why a car coasts to a stop on a flat road.

**Aero drag / frontal area / Cd** — aerodynamic drag force grows with the square of speed, and depends on the car's frontal area (m²) and drag coefficient (Cd, a shape-efficiency number — lower is more slippery through the air).

## Suspension (`suspension/`, `specs/suspension.py`, `specs/linkage.py`)

**Double wishbone** — a suspension design using two roughly-triangular control arms (upper and lower) per wheel, each pivoting on the chassis at one end and connecting to the wheel's upright at the other. Used on this car's front axle; offers strong control over camber through suspension travel.

**Multi-link ("Integral Axle")** — a suspension design using several (often 4-5) individual links instead of two wishbones, giving engineers more independent control over how the wheel moves (camber vs. toe vs. longitudinal compliance) at the cost of complexity. Volvo's name for this car's rear suspension; the extra links are specifically used here to give passive toe-in under load for stability, more than for camber control.

**Sprung / unsprung mass** — sprung mass is everything supported *by* the springs (body, engine, passengers); unsprung mass is everything *not* supported by them (wheels, tires, brake rotors, the outer ends of control arms). Unsprung mass matters because it doesn't benefit from spring/damper isolation — it just gets thrown around by bumps directly.

**Ride frequency** — how many times per second the sprung mass would bounce on its springs if disturbed (like a mass on a spring). Used here to *derive* spring rates: pick a target comfort-oriented frequency (~1.3-1.4 Hz), then back-calculate the spring rate needed to produce it given the sprung mass.

**Anti-roll bar (ARB)** — a torsion bar connecting the left and right suspension, which does nothing when both sides compress equally (straight-line bump) but resists strongly when they compress *differently* (cornering roll) — its whole job is fighting body roll without stiffening the ride over bumps.

**Bump / droop (jounce / rebound)** — bump (jounce) is the suspension compressing (wheel moving up relative to the body); droop (rebound) is it extending (wheel moving down/away). Both have mechanical travel limits (bump stops / droop stops) beyond which the suspension gets sharply stiffer.

**Camber** — the tilt of a wheel from vertical, viewed from the front. Negative camber = top of the tire leans inward. A cambered tire generates some sideways force even at zero slip angle (see "camber thrust" below), and cornering grip is generally best with a bit of negative camber on the loaded/outer tire.

**Camber thrust** — the small lateral force a tire generates purely from being cambered, independent of slip angle — modeled here as a force proportional to camber angle and normal load.

**Toe (toe-in / toe-out) / bump steer** — toe is whether a wheel points slightly inward (toe-in) or outward (toe-out) relative to straight-ahead, when viewed from above. "Bump steer" is toe angle *changing* as the suspension travels through bump/droop — an unintended (or deliberately designed-in) steering effect that happens without the driver touching the wheel.

**Roll center** — the height (per axle) about which the car's body appears to roll during cornering, determined entirely by suspension linkage geometry (not by the CG or springs). The distance between the CG and the roll axis (the line connecting front and rear roll centers) is the actual lever arm for how much roll a given cornering force produces — using raw CG-height-above-ground instead overstates the roll moment.

**Instant center / swing arm (equivalent)** — a simplified hand-calculation technique (see Milliken & Milliken's *Race Car Vehicle Dynamics*) for suspension kinematics: extend the lines of the upper and lower control arms until they cross — that crossing point is the "instant center," and the whole double-wishbone assembly then behaves, for small movements, like a single wheel swinging on an arm of that length pivoting about that point. Used here (`linkage_geometry.py`) to derive camber gain and roll center from actual arm-pivot coordinates, instead of guessing a flat gain curve.

**Anti-dive / anti-squat** — suspension link geometry angled (in side view) so that some of the weight-transfer moment from braking (anti-dive) or accelerating (anti-squat) gets reacted directly through the rigid links instead of showing up as visible body pitch through the springs. This is why a well-designed car dives/squats *less* than its spring rate alone would suggest.

**K&C (Kinematics & Compliance)** — the general term for how a suspension's geometry (kinematics) and rubber-bushing flex (compliance) together determine camber/toe/roll-center behavior through travel and under load; the industry umbrella term for everything in this section.

## Steering & Handling (`steering/`, `specs/steering.py`)

**Ackermann geometry** — the principle that, in a turn, the inside wheel must steer at a sharper angle than the outside wheel, because it's tracing a smaller circle. A steering linkage designed to (approximately) satisfy this is called "Ackermann steering."

**Steering ratio** — how many degrees the steering wheel turns for one degree of actual road-wheel turn (e.g., 19:1 here). Derived in this project from Volvo's published turning circle and the car's wheelbase, rather than guessed outright.

**Understeer / oversteer** — understeer: the car turns *less* than the driver's steering input suggests it should (front tires run out of grip first, nose "pushes" wide). Oversteer: the car turns *more* than commanded (rear tires lose grip first, tail steps out). ESC's whole job is detecting and correcting whichever one is happening.

## Vehicle Dynamics (`chassis/vehicle_body.py`, `sim/simulation.py`)

**Yaw rate** — how fast the car is rotating about its vertical axis (degrees or radians per second) — i.e., how fast it's actually turning, as opposed to how much the wheels are steered.

**Sideslip (angle)** — the angle between the direction the car's body is pointed and the direction its center of mass is actually moving. Small and barely noticeable in normal driving; large during a slide/drift.

**CG (center of gravity)** — the single point where the vehicle's entire mass can be considered concentrated for the purposes of force/moment calculations. Its height above the ground and position between the front/rear axles drive almost every weight-transfer calculation in this project.

**Bicycle model / single-track model** — a classic simplification that collapses each axle's two wheels into one, turning the vehicle into an idealized two-wheeled "bicycle" for lateral dynamics analysis. This project started with this simplification and later replaced it with genuine independent 4-wheel modeling, but the term appears in earlier design notes.

**3-DOF (degrees of freedom)** — a model tracking exactly three independent motions. Used twice here for different things: the vehicle body's 3-DOF is longitudinal + lateral + yaw (how it moves across the ground); the suspension's 3-DOF is heave + pitch + roll (how the body moves relative to its own wheels).

**Body frame vs. world frame** — body-frame quantities (like `vx`, `vy`) are measured along the car's own forward/sideways axes, which rotate with the car; world-frame quantities (`world_x`, `world_y`, heading) are measured against a fixed map-like reference. Converting between them (via the heading angle) is what lets a steering input trace an actual plottable path.

## Electronics / CAN Bus (`network/`, `ecu/`, `dsc/`)

**CAN bus (Controller Area Network)** — the standard wired network real cars use for their onboard computers (ECUs) to talk to each other, broadcasting small fixed-format messages that any module can listen to.

**Arbitration ID** — the numeric identifier at the front of every CAN message, used both to say "this is an ENGINE_DATA message" and (in real hardware) to resolve which message wins if two try to send at once (lower ID = higher priority).

**DLC (Data Length Code)** — how many bytes of actual data a CAN message carries; classic CAN caps this at 8 bytes per frame, which this project's message definitions respect.

**Byte-packing / scale + offset encoding** — real CAN signals aren't sent as floating-point numbers; a physical value (like 5700 rpm) gets converted to a raw integer via `raw = (value - offset) / scale`, packed into 1-4 bytes, and reversed on the receiving end. `CANSignal` in this project implements exactly this.

**ECU (Electronic Control Unit)** — any of the small onboard computers running a car's systems (engine, transmission, brakes, etc.). In this project, each `ECU` subclass reads live simulation state and broadcasts it on the bus on a schedule, mirroring how a real ECU reports sensor readings.

**DSTC (Dynamic Stability and Traction Control)** — Volvo's marketing name for its bundled stability/traction control system, covering what other manufacturers call ESC + TCS + ABS together.

**TCS (Traction Control System)** — cuts engine power (or brakes a spinning wheel) when a driven wheel loses traction under acceleration, to stop wheelspin.

**ABS (Anti-lock Braking System)** — releases and reapplies brake pressure at an individual wheel many times per second to prevent it locking up under hard braking, preserving steering control and (usually) shortening stopping distance.

**ESC (Electronic Stability Control)** — compares how the car is *actually* rotating (yaw rate) against how much it *should* be rotating given the steering input and speed, then brakes one specific wheel to correct the difference if the two disagree by too much (see understeer/oversteer above).

**Reluctor ring / pulse quantization** — real wheel speed sensors don't measure speed directly; they count magnetic pulses as a toothed ring spins past a sensor, then infer speed from the pulse rate. This means speed readings are quantized to whole pulses per sample window — and notoriously imprecise at low speed, since few pulses occur in a short window.

**Select-high / select-low / median select** — real ABS/TCS/ESC systems, lacking a true "ground truth" vehicle speed sensor (especially on AWD cars with no non-driven wheel), estimate it from the 4 wheel speeds using a robust statistic (median here) that resists being thrown off by any single wheel spinning or locking.

## Body Control Module (`body/`, `ecu/body_ecu.py`, `specs/body.py`)

**BCM (Body Control Module)** — the real ECU responsible for a car's "comfort/convenience" electronics: doors, locks, lights, wipers, power windows, tailgate, rather than powertrain or chassis dynamics. `xc90_sim/body/Closures` models this domain's core state/timers.

**Closure** — automotive term for any body panel that opens (door, hood/bonnet, trunk/tailgate) — grouped together because they share the same concerns: latch state, ajar warnings, and (for powered ones) actuation timers.

**Ajar warning** — the real dashboard warning/chime that fires when any closure isn't fully latched, especially while the vehicle is moving; modeled here as `Closures.ajar_warning()`.

**Power tailgate / power liftgate** — a motorized trunk/tailgate that opens and closes itself over several real seconds when commanded (button, key fob, or hands-free kick sensor), rather than swinging open instantly like a manual one — a standard feature on this car's Momentum trim.

**Central locking** — one lock/unlock command applied to every door at once, rather than each door having to be locked individually; real systems (and this one) refuse to lock while any door is standing open.

**Auto door lock** — a real, factory-enabled Volvo feature that automatically locks all doors once the car is moving above a threshold speed, provided every door is already shut.

## Cabin Electronics (`cabin/`, `ecu/cabin_ecu.py`, `specs/cabin.py`)

**HVAC (Heating, Ventilation, and Air Conditioning)** — the climate control system. Modeled here as a real first-order thermal system: cabin temperature evolves each tick from ambient heat exchange plus HVAC output, not just a setpoint display — see `cabin/hvac.py`.

**Lumped thermal mass / UA value** — a simplification technique for thermal systems: instead of modeling every surface (glass, seats, dash, air) individually, collapse the whole cabin to one effective heat capacity (how much energy it takes to change its temperature by 1°C) and one effective heat-loss coefficient to the outside (UA, in W/°C) — the same "one number stands in for a whole assembly" approach used elsewhere in this project (e.g. pitch/roll inertia).

**Park Assist / parking sensors** — ultrasonic sensors that measure distance to a nearby obstacle and warn the driver with an increasingly rapid tone as the gap closes; modeled here as a sensor/warning layer only (no automated self-parking steering, which is a much larger robotics problem).

**Cruise control** — a closed-loop feature: once engaged, the car's own throttle/brake logic drives to hold a set speed automatically, rather than the driver's foot doing it — see `cabin/controls.py`'s `CruiseController`. Pressing the brake pedal cancels it, same as a real car.

**Seatbelt reminder** — the real safety feature that warns for any seat detected as occupied (via a weight sensor, in a real car) but not buckled; modeled here from each seat's `occupied`/`seatbelt_buckled` state.

**BLIS (Blind Spot Information System)** — Volvo's own real feature and name for a blind-spot warning system: detects a vehicle in either rear side blind spot and warns the driver, typically via a light in the corresponding side mirror. Disabled below a minimum speed, same as the real feature, to avoid false positives in parking-lot-speed maneuvering.

## Gear Selector & Lighting (`transmission/gear_selector.py`, `body/lighting.py`, `body/windows.py`, `body/mirrors.py`)

**PRND** — Park/Reverse/Neutral/Drive, the gear selector positions on an automatic transmission — a different, higher-level concept than the transmission's own 1-8 forward gear ratios, which only matter once the selector is in Drive.

**Brake-shift interlock (BTSI)** — a real safety feature that won't let the driver move the gear selector out of Park unless the brake pedal is pressed, preventing an unintended rollaway.

**Wheel lockup** — when brake torque exceeds what the tire's friction can resist, the wheel stops rotating relative to the axle (while the vehicle may still be sliding) rather than continuing to spin freely — this project's ABS models the release/reapply response to exactly this condition.

**DRL (Daytime Running Lights)** — low-intensity lights that run automatically whenever the vehicle is on and the headlights aren't manually switched to low/high beam, for daytime visibility.

**One-touch window** — a power window feature where a single tap (rather than holding the switch) runs the window all the way up or down on its own.

**Ignition states (OFF / ACCESSORY / cranking / RUN)** — the rotary knob's positions: OFF is fully shut down; ACCESSORY powers infotainment/HVAC without the engine running; cranking is the brief starter-motor spin-up; RUN is the engine actually running. A brake-to-start interlock requires the brake pedal pressed to leave OFF/ACCESSORY.

**Park Assist Pilot** — Volvo's real feature/name for semi-autonomous parallel parking: the system steers the car into a detected gap while the driver (or, here, an automatic slow creep) controls speed — a genuine steering-angle takeover, not just a sensor warning.

**Two-phase parallel-park technique** — the classic manual parking method this project's simplified pilot algorithm is based on: turn the wheel to full lock toward the curb and reverse until the car's heading has rotated to roughly a 30-40° angle, then countersteer to full lock the other way and reverse back until parallel with the curb again.

**Low-speed collision mitigation** — an automatic throttle-cut and brake application triggered by a critically close obstacle, overriding the driver's own pedal input — a simplified version of what Volvo's City Safety does at parking speed.

**Engine Auto Start/Stop** — a fuel-saving feature that shuts the engine off while stopped (in Drive/Neutral, brake held) and restarts it automatically the instant the driver needs to move — distinct from the ignition itself being off: accessories, infotainment, and HVAC all stay fully powered throughout.

**Fold-flat seat** — a 2nd/3rd row seat that folds down flush with the cargo floor to expand luggage space, standard on most 3-row SUVs including this one; distinct from ordinary recline, since a folded seat isn't usable to sit in.

**Sunshade/cover (sunroof)** — the powered interior panel that blocks light through a sunroof independently of the glass panel itself; on most real sliding sunroofs, opening the glass panel requires the shade to open first since the glass physically retracts into the same space.

**Intermittent wiper** — a wiper speed setting that pauses between sweeps rather than running continuously, for light rain.

**TPMS (Tire Pressure Monitoring System)** — a federally mandated (FMVSS 138 in the US) system that warns the driver when any tire's pressure drops too far below the vehicle's recommended cold pressure (25% low is the real regulatory threshold), reading each wheel's pressure independently.

**Oil life monitor** — a real dashboard feature that counts down a percentage based on miles driven since it was last reset, not a literal continuous sensor measuring oil quality; a technician resets it via a service menu after an actual oil change.

**Infotainment screen / menu page** — the different pages of a touchscreen infotainment system (Climate, Park Assist, Seats, Car Status, etc.), each showing and controlling a different vehicle subsystem — modeled here as `Infotainment.current_screen` plus an aggregator that pulls in whatever that screen needs to show.

## Engine Combustion (`engine/cylinder.py`, `engine/camshaft.py`, `specs/cylinder.py`)

**Slider-crank geometry** — the mechanical relationship between crank angle, connecting rod length, and piston position; used to compute exactly where the piston is (and how fast the cylinder volume is changing) at any point in the engine's rotation.

**TDC / BDC (Top Dead Center / Bottom Dead Center)** — the piston's two extreme positions: fully up (smallest cylinder volume) and fully down (largest cylinder volume).

**Valve overlap** — the brief period around TDC (between the exhaust and intake strokes) where both the intake and exhaust valves are open at once — a real, deliberate feature of camshaft timing, not a flaw.

**Single-zone combustion model** — a simplified (but genuinely physics-based) way to model in-cylinder combustion: treats the entire cylinder's gas as one uniform blob (one pressure, one temperature) rather than tracking a spreading flame front in detail (a "multi-zone" or full CFD model would do that). The standard technique for engine simulation when full 3D combustion modeling isn't warranted.

**Wiebe function** — the standard mathematical curve (from combustion engineering) describing how quickly fuel burns after spark, as a fraction of total fuel burned vs. crank angle — starts slow, accelerates, then tapers off, matching how a real flame front spreads and then runs out of room.

**MAP (Manifold Absolute Pressure)** — the actual air pressure inside the intake manifold feeding the cylinders — higher than atmospheric when boosted, lower ("vacuum") at a closed throttle. A standard real OBD2-readable sensor value.

**Volumetric efficiency (VE)** — how much air actually gets trapped in a cylinder compared to the theoretical maximum implied by manifold pressure and cylinder volume — real engines never achieve 100% due to valve-flow restrictions and timing.

**AFR (Air-Fuel Ratio)** — the mass ratio of air to fuel in the cylinder; 14.7:1 ("stoichiometric") is the ideal complete-combustion ratio for gasoline; real engines run richer (more fuel) than that under boost/high load for cooling and knock protection.

**Idle Air Control (IAC)** — the real system (a small valve or, on modern cars, the electronic throttle itself) that maintains a minimum idle airflow independent of the driver's foot, keeping the engine from stalling at idle.

**BSFC (Brake Specific Fuel Consumption)** — a map of how efficiently an engine converts fuel to useful power across every combination of rpm and load; real engines are meaningfully less efficient at very light loads than at their best operating point, an effect a simple friction-torque curve doesn't fully capture.

**Flywheel** — the rotating disc bolted to the back of the crankshaft that smooths out the crank's speed pulsations between combustion pulses (and, in a manual/Geartronic-equipped car, provides the surface the clutch or torque converter grabs onto).

**Timing belt / timing chain** — the mechanical link (a toothed rubber belt or a metal chain, depending on the engine) that keeps the camshaft turning at exactly half crankshaft speed, so the valves open and close in sync with piston position. This car uses a belt, with a real scheduled replacement interval (a belt failing is catastrophic, unlike gradual tire/brake wear) — a chain is normally considered lifetime/maintenance-free.

**Accessory (serpentine) belt** — the separate belt (not the timing belt) that drives engine-external accessories like the alternator and AC compressor off crank rotation.

**Alternator** — converts mechanical rotation (from the accessory belt) into electrical power to run the car's electronics and recharge the battery; the more electrical demand (headlights, blower fan, etc.), the more mechanical torque it draws from the engine.

**GDI (Gasoline Direct Injection)** — a fuel system that injects fuel directly into the combustion chamber at high pressure (this engine, ~150 bar), rather than into the intake port at low pressure like older "port injection" systems.

**Fuel rail pressure** — the actual pressure the fuel injectors are fed at; built up by the fuel pump and required to be near its target before injectors can deliver their commanded fuel amount accurately.

**Pulse width (fuel injection)** — how long, in milliseconds, an injector's solenoid holds it open per injection event — the actual quantity a real ECU calculates and commands, since a fixed-size injector's total fuel delivered is proportional to how long it stays open.

**AGM battery (Absorbent Glass Mat)** — a type of 12V lead-acid battery that tolerates frequent full discharge/recharge cycling much better than a traditional flooded battery — a real requirement for any car with genuine Auto Start/Stop, since that feature cycles the electrical system far more often than normal driving.

**State of charge (SoC)** — how full a battery is, as a percentage of its total capacity — the battery equivalent of a fuel gauge.

## Exhaust System (`exhaust/exhaust_system.py`, `exhaust/oxygen_sensor.py`, `exhaust/egr_valve.py`, `specs/exhaust.py`)

**Catalytic converter / light-off temperature** — the catalytic converter is the exhaust-system component that chemically converts pollutants (CO, NOx, unburned hydrocarbons) into less harmful gases; it only works once its ceramic substrate reaches "light-off temperature" (the real reason cold-start emissions are worse than warmed-up emissions). Modeled here as a temperature that heats up on a real thermal time constant once the engine's running.

**Backpressure** — resistance to exhaust flow created by the catalytic converter and muffler; the engine has to do a small amount of extra work pushing exhaust gas out against it during the exhaust stroke, a real (if usually small) pumping loss.

**O2 / lambda sensor** — a sensor in the exhaust stream that reads how rich or lean the actual combustion mixture was (lambda = 1.0 means exactly stoichiometric — see AFR, below), the real signal an ECU uses for closed-loop fuel trim. Modeled here with a real response lag and measurement noise, same "sensors aren't perfect" treatment as `WheelSpeedSensor`.

**EGR (Exhaust Gas Recirculation)** — a real emissions-control system that routes a small amount of exhaust gas back into the intake to reduce combustion temperatures and NOx formation. Modeled here via two real mechanisms: (1) a reduction in effective trapped fresh charge — the recirculated exhaust gas physically displaces fresh intake air in the manifold, a volumetric-efficiency derating — and (2) a lower effective specific-heat ratio (gamma) for the diluted charge during compression, since recirculated exhaust gas (mostly triatomic CO2/H2O) has a lower gamma than fresh air. Still a deliberate simplification short of a full multi-species thermodynamic model — there's no separately tracked species/composition/heat-capacity through the combustion energy balance, just one blended effective gamma plus the displacement effect — but it's genuinely two real mechanisms now, not one.

## Airbags/SRS (`cabin/airbags.py`, `specs/airbags.py`)

**SRS (Supplemental Restraint System) / airbags** — the crash-sensing and airbag-deployment system. Modeled here reading real body-frame accelerometer data against a simple instantaneous-g deployment threshold, since this project has no actual collision/contact physics (no obstacles to crash into) to generate a real crash pulse from — an honest simplification of a real algorithm that's proprietary and integrates the crash-pulse shape over tens of milliseconds, not a single g threshold.

**Occupant Classification System (OCS)** — a real system that senses whether a seat is occupied (and, on more advanced systems, whether by a child seat) to decide whether that seat's airbag should deploy at all; an empty passenger seat suppresses the passenger airbag, and a detected child seat suppresses it too even while the seat reads occupied. Modeled here at both levels: `Seat.occupied` gates deployment (an empty seat suppresses it), and `Seat.child_seat_installed` (externally set, same pattern as `occupied`/`seatbelt_buckled`) suppresses passenger-frontal deployment on an occupied seat as well — the real OCS behavior.

**Pretensioner** — a pyrotechnic device that instantly takes up slack in a seatbelt at the moment of a crash, before the airbag itself deploys, to pull the occupant firmly into the seat. Fires here for every occupied and buckled seat whenever any airbag deploys.

**SRS self-test / bulb-check** — the brief dashboard-light illumination every SRS system runs through when the car is first powered on, confirming the warning light's bulb itself works before going dark (assuming no fault) — the same idea as any other dashboard "bulb check." Modeled here as a real timed window after power-on, plus a fault-injection flag standing in for the diagnostic-trouble-code conditions (buckle-switch continuity, clockspring fault, etc.) this project doesn't model the wiring-level physics of.

## Drivetrain Hardware (`drivetrain/propshaft.py`, `transmission/transmission_fluid.py`, `drivetrain/cv_joint.py`, `drivetrain/wheel_bearing.py`)

**Propshaft / driveshaft windup, torsional stiffness** — "windup" is the small torsional twist a driveshaft develops under load, like a twisted rubber band, before it fully transmits torque from one end to the other; "torsional stiffness" (Nm of torque per radian of twist) is the shaft-geometry property that determines how much windup a given torque produces — stiffer shaft, less windup. Modeled here as a real angle computed from rear-axle torque, and (as of 2026-09-01) fed back into the actual torque path: the shaft's own lagged twist state is read back out as a real delivered torque, so a hard launch or a gearshift sees torque delivery smoothed/delayed slightly by the shaft's compliance rather than arriving instantaneously. The stiffness constant itself was originally a bare guess 5x too soft (producing implausible ~40° of windup at peak torque before being re-derived from real tubular-shaft geometry down to ~8-9°) — see `STATUS.md`'s "Bugs found and fixed" for the full story.

**Transmission cooler** — the dedicated small heat exchanger (separate from the engine's own radiator) that removes heat from automatic transmission fluid, typically using airflow but with no fan of its own the way the engine radiator has — so it has a lower stationary heat-rejection floor than the radiator does. Modeled as its own airflow-dependent object (ram air, saturating at speed) rather than a single fixed number.

**ATF / transmission fluid** — the specialized oil inside an automatic transmission that both lubricates it and, inside the torque converter, is the actual fluid doing the pump-to-turbine power transfer. It heats up from real torque-converter slip losses and is cooled by the dedicated transmission cooler above, same as a real car's.

**CV joint (constant-velocity joint)** — a joint that lets a half-shaft transmit power at a constant rotational speed even while operating at a changing angle — needed on this car's front half-shafts because those wheels are both driven and steered. A worn or steeply-angled CV joint has a small, real efficiency loss.

**Wheel bearing** — the bearing that lets each wheel spin freely on its hub while carrying the vehicle's weight; as it wears it develops a modest amount of extra rolling resistance (and eventually noise/play, not modeled here).

## Radar-Based ADAS (`cabin/adaptive_cruise.py`, `cabin/lane_keeping_assist.py`, `specs/adas.py`)

**ACC (Adaptive Cruise Control) / follow-distance / time gap** — a cruise control that not only holds a set speed but also automatically slows to maintain a gap behind a detected vehicle ahead, speeding back up toward the set speed once the way is clear. "Time gap" is the real way ACC systems express desired following distance — a number of seconds behind the car ahead (so the actual distance scales with speed), rather than a fixed number of meters. Modeled here as a target-speed calculation layered on top of this project's existing `CruiseController` — no new pedal-control logic, just a smarter speed target.

**Lane-keeping assist / Pilot Assist** — a steering-assist feature (Volvo's real name for its version is Pilot Assist) that reads the car's position within its lane and applies a small corrective steering nudge to keep it centered, backing off entirely for a driver's own deliberate steering input (a turn, an intentional lane change) — an assist, not an autopilot. Distinct from Park Assist Pilot (see above), which takes over steering completely during a parking maneuver.

## Vehicle Identity (`specs/vehicle_identity.py`)

**VIN (Vehicle Identification Number)** — the unique 17-character serial number assigned to every individual vehicle; this project models one specific real VIN, not a generic "average" XC90.

**Trim** — the specific equipment/feature package a car was sold with (e.g., "T6 Momentum" vs. "T6 Inscription") — different trims of the same model can have meaningfully different curb weight, wheel size, and equipment, which is why getting the trim right mattered for this project's mass and tire-size corrections.

**CARFAX** — a commercial vehicle-history report service; used here as a source for this specific car's real VIN, trim, mileage, and service/accident history (not for engineering specs like weight or tire size, which come from Volvo's own published data).
