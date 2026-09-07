# XC90 digital twin — interactive 3D UI

A local web app that puts a real, live `xc90_sim.Simulation` behind a
browser UI. Every interaction (hood, doors, tailgate, battery disconnect,
engine removal, pulling a fuse or relay) calls a real `Simulation` method
and mutates the actual sim state — this is not a mockup wired to fake
state, it's the same object a Python script driving `xc90_sim` directly
would see and change.

## Run it

```
python3 web_ui/server.py
```

Then open http://localhost:8765/ in a browser. No extra dependencies —
the backend is Python stdlib only (`http.server`), matching this
project's numpy-only core.

## How it works

- `server.py` holds one `Simulation` instance and steps it in a
  background thread in real time (50Hz, same as the rest of this
  project), so the car keeps idling/cooling/discharging even between UI
  clicks — the same as leaving a real car sitting with the key on.
- The browser polls `GET /state` every 200ms for a telemetry snapshot,
  and posts `POST /action` (`{"action": "toggle_hood"}` etc.) for every
  interaction. Every action handler in `server.py`'s `_do_action()` calls
  a real `Simulation` method — see that function for the exact mapping.
- The frontend (`static/index.html`) is a Three.js scene: a
  correctly-proportioned (wheelbase 2.984m, real) but simplified car body
  — not a photorealistic model, since no licensed 3D asset of the real
  car exists to build from — with an openable hood revealing a clickable
  engine bay (engine block, battery, an 8-circuit fuse box, a 5-relay
  box), openable doors/tailgate, and a HUD panel with live telemetry.

## Verified vs. not

The backend (every action's real effect on the simulation) is verified
end-to-end via direct HTTP calls — hood open/close, engine start/stop,
pulling a fuse, disconnecting the battery, and removing the engine were
each confirmed to produce the real, correct downstream simulation
behavior (e.g. removing the engine mid-run genuinely decays rpm to zero
even though the ignition switch itself stays in "run" — a real, honest
distinction between the key state and the engine's physical ability to
turn). The 3D frontend's visual rendering has NOT been visually verified
(no way to render a browser here) — the code follows standard Three.js
r128 patterns and passes a basic syntax/bracket-balance check, but if
something looks wrong when you actually open it, that's the part to
debug first.

## What's wired so far

- **Body**: hood, all 4 doors, power tailgate (real `Closures` state)
- **Electrical**: main battery disconnect/reconnect, 8 real fuse
  circuits (pull/replace), 5 real relays (disconnect/reconnect)
- **Engine**: start/stop (real cranking sequence), full physical removal
  (a new mechanic added for this UI — see `Simulation.set_engine_removed()`)

## What's not wired yet

This was scoped as a first working slice, not full "every part"
coverage (that's explicitly the stated end goal, not yet complete):
- Windows, mirrors, sunroof, lighting circuits (all real in `xc90_sim`,
  just not yet exposed as clickable 3D parts or HTTP actions here)
- Individual belt/hose/component removal beyond the whole-engine mechanic
- Interior (seats, HVAC, infotainment) — no 3D interior modeled at all
- A dashboard/instrument cluster visualization beyond the HUD text panel
