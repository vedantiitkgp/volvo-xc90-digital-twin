"""
Local web server bridging a real, live xc90_sim.Simulation to a browser UI.

Stdlib-only (no new dependency on this project's numpy-only core) —
http.server + a background thread stepping the simulation in real time.
The UI polls GET /state and posts GET-free JSON actions to POST /action;
every action calls a REAL Simulation method (hood/doors/battery/engine/
fuse/relay), so what happens in the browser is the same state a script
driving xc90_sim directly would see and change.

Run: python3 web_ui/server.py
Then open http://localhost:8765/ in a browser.
"""

import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# .glb/.gltf aren't in Python's builtin mimetypes database on every
# platform; a small explicit map covers everything static/ actually needs.
_CONTENT_TYPES = {
    ".html": "text/html", ".js": "application/javascript", ".css": "text/css",
    ".glb": "model/gltf-binary", ".gltf": "model/gltf+json", ".bin": "application/octet-stream",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
}


def _guess_content_type(path):
    _, ext = os.path.splitext(path)
    return _CONTENT_TYPES.get(ext.lower(), "application/octet-stream")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xc90_sim.sim.simulation import Simulation  # noqa: E402

PORT = int(os.environ.get("PORT", 8765))
TICK_DT = 0.02
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

sim = Simulation()
sim_lock = threading.Lock()


def _run_sim_loop():
    """Steps the real simulation in real time, in the background, so the
    car keeps behaving (idling, cooling, discharging) even between UI
    actions -- same as leaving a real car sitting with the key on."""
    while True:
        start = time.monotonic()
        with sim_lock:
            sim.step(TICK_DT)
        elapsed = time.monotonic() - start
        time.sleep(max(0.0, TICK_DT - elapsed))


def _snapshot_state():
    with sim_lock:
        t = sim.telemetry()
        return {
            "time_s": round(sim.time_s, 2),
            "ignition_state": sim.ignition.state,
            "engine_running": sim.ignition.engine_running,
            "engine_rpm": round(sim.engine.rpm, 0),
            "speed_mph": round(t["speed_mph"], 1),
            "gear_selector": sim.gear_selector.position,
            "transmission_gear": t["gear"],
            "converter_locked": t["converter_locked"],
            "engine_auto_stopped": t["engine_auto_stopped"],
            "brake_on": sim._manual_brake > 0.5,
            "world_x_m": t["world_x_m"],
            "world_y_m": t["world_y_m"],
            "distance_m": t["distance_m"],
            "heading_deg": t["heading_deg"],
            "steering_wheel_deg": t["steering_wheel_deg"],
            "hood_open": sim.closures.hood_open,
            "door_open": dict(sim.closures.door_open),
            "tailgate_open": sim.closures.tailgate_open,
            "tailgate_target_open": sim.closures.tailgate_target_open(),
            "tailgate_progress_frac": sim.closures.tailgate_progress_frac(),
            "sunroof_glass_state": sim.sunroof.glass_state,
            "sunroof_glass_target": sim.sunroof.glass_target(),
            "sunroof_glass_progress_frac": sim.sunroof.glass_progress_frac(),
            "sunroof_shade_open": sim.sunroof.shade_open,
            "sunroof_shade_target": sim.sunroof.shade_target(),
            "sunroof_shade_progress_frac": sim.sunroof.shade_progress_frac(),
            "engine_removed": t["engine_removed"],
            "battery_disconnected": t["battery_disconnected"],
            "battery_charge_pct": t["battery_charge_pct"],
            "support_battery_charge_pct": t["support_battery_charge_pct"],
            "blown_fuses": t["blown_fuses"],
            "pulled_fuses": t["pulled_fuses"],
            "relay_faults": t["relay_faults"],
            "coolant_temp_c": t["coolant_temp_c"],
            "fuel_level_frac": t["fuel_level_frac"],
            "washer_fluid_l": t["washer_fluid_l"],
            "washer_fluid_low_warning": t["washer_fluid_low_warning"],
        }


def _do_action(name, payload):
    """Every branch here calls a real xc90_sim.Simulation method — no
    action here is decorative, each one mutates the live sim state."""
    with sim_lock:
        if name == "toggle_hood":
            sim.set_hood(not sim.closures.hood_open)
        elif name == "toggle_door":
            corner = payload["corner"]
            sim.set_door(corner, not sim.closures.door_open[corner])
        elif name == "toggle_tailgate":
            sim.request_tailgate(not sim.closures.tailgate_open)
        elif name == "toggle_sunroof":
            # Real mechanical interlock lives in Sunroof itself (opening the
            # glass auto-opens the shade first) -- this just picks the target.
            sim.request_sunroof_glass("closed" if sim.sunroof.glass_state != "closed" else "open")
        elif name == "start_engine":
            sim.set_driver_inputs(throttle=0.0, brake=1.0)
            sim.start_engine()
        elif name == "stop_engine":
            sim.stop_engine()
        elif name == "set_gear":
            # Real safety interlock lives in GearSelector itself (e.g. won't
            # leave Park without the brake pedal held) -- this just forwards
            # the request, same as a driver moving the shifter.
            sim.set_gear_selector(payload["position"])
        elif name == "set_throttle":
            sim.set_driver_inputs(throttle=float(payload["value"]), brake=0.0)
        elif name == "set_brake":
            sim.set_driver_inputs(throttle=0.0, brake=1.0 if payload["on"] else 0.0)
        elif name == "set_steering":
            sim.set_steering_wheel_angle_deg(float(payload["angle_deg"]))
        elif name == "toggle_battery":
            sim.set_battery_disconnected(not sim.battery.disconnected)
        elif name == "toggle_engine_removed":
            sim.set_engine_removed(not sim.engine_removed)
        elif name == "toggle_fuse":
            fname = payload["name"]
            fuse = sim.fuse_box.fuses[fname]
            if fuse.pulled:
                sim.replace_fuse(fname)
            else:
                sim.pull_fuse(fname)
        elif name == "toggle_relay":
            rname = payload["name"]
            relay = sim.relay_box.relays[rname]
            if relay.stuck_open:
                sim.reconnect_relay(rname)
            else:
                sim.disconnect_relay(rname)
        elif name == "refill_washer_fluid":
            sim.refill_washer_fluid()
        else:
            raise ValueError(f"unknown action: {name!r}")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # quiet — telemetry polling would otherwise spam the console

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/state":
            self._send_json(_snapshot_state())
        elif self.path in ("/", "/index.html"):
            self._serve_static("index.html", "text/html")
        elif self.path.startswith("/static/"):
            # Serves everything under static/ (the page itself, and its
            # assets — models/*.glb in particular) by real file extension,
            # not just the one hardcoded index.html route above.
            rel_path = self.path[len("/static/"):].split("?", 1)[0]
            self._serve_static(rel_path, _guess_content_type(rel_path))
        elif self.path.startswith("/models/"):
            # Also serves /models/ directly (same as /static/models/) so
            # that the GitHub Pages build (which strips the /static/ prefix)
            # can load .glb assets without a redirect.
            rel_path = "models/" + self.path[len("/models/"):].split("?", 1)[0]
            self._serve_static(rel_path, _guess_content_type(rel_path))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/action":
            length = int(self.headers.get("Content-Length", 0))
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
                _do_action(body["action"], body)
                self._send_json({"ok": True, "state": _snapshot_state()})
            except (KeyError, ValueError) as exc:
                self._send_json({"ok": False, "error": str(exc)}, status=400)
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_static(self, filename, content_type):
        path = os.path.normpath(os.path.join(STATIC_DIR, filename))
        if not path.startswith(os.path.normpath(STATIC_DIR)):
            self.send_response(404)  # reject path traversal (e.g. "../../")
            self.end_headers()
            return
        try:
            with open(path, "rb") as f:
                body = f.read()
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    threading.Thread(target=_run_sim_loop, daemon=True).start()
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"XC90 sim UI running at http://localhost:{PORT}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
