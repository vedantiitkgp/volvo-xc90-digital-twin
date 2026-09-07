"""
Live routing: turns two real addresses into a drive cycle built from an
actual route's real turn-by-turn segments and real traffic-signal/stop-sign
locations — not a generic style-block guess. Uses free public APIs that
need no API key or account:

  - Nominatim (nominatim.openstreetmap.org) — geocoding, address -> lat/lon.
  - OSRM demo server (router.project-osrm.org) — routing: real per-segment
    distance/duration/maneuver type, and route geometry.
  - Overpass API (overpass-api.de) — queries OpenStreetMap directly for
    traffic_signals/stop-sign nodes near the route.
  All data (c) OpenStreetMap contributors, ODbL 1.0 (http://osm.org/copyright).

These are shared public services meant for light/occasional use, not
production traffic — this module makes at most 2 geocoding calls + 1
routing call + 1 Overpass call per trip, and sleeps between geocoding calls
to respect Nominatim's documented 1-request/second policy.

HTTP fetching goes through `curl` via subprocess rather than urllib/requests
directly. This isn't a style choice: on this machine, Python's stdlib ssl
module is linked against LibreSSL 2.8.3 (macOS system Python, ~2018-era),
which fails to negotiate TLS with router.project-osrm.org (`SSLV3_ALERT_
HANDSHAKE_FAILURE`) — confirmed to affect both `urllib.request` and
`requests`/urllib3 identically, since they share the same underlying ssl
module. `curl` succeeds because macOS links it against a different, current
TLS stack. If you're running a Python whose ssl module doesn't have this
problem, swapping `_http_get_json`/`_http_post_json` for urllib/requests
calls works exactly the same way.

What this does NOT model: real-time traffic conditions (OSRM's default
profile is a free-flow time estimate), and signal timing/phase (a fetched
signal always costs a flat expected delay here — see SIGNAL_EXPECTED_DELAY_S
— rather than modeling the real chance of catching it green).
"""

import json
import math
import subprocess
import time
import urllib.parse

from .drive_cycle import DriveCycle

USER_AGENT = "xc90-sim/1.0 (personal vehicle-dynamics simulation project)"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Drive-cycle construction constants. ASSUMPTION — comfortable-driving values,
# not measurements; see drive_cycle.py for the same kind of assumption made
# for the synthetic (non-live-routed) cycle generator.
ACCEL_MPS2 = 1.8
DECEL_MPS2 = 2.2
TURN_SPEED_MPS = 7.0  # ~25 kph, typical speed through an actual turn
NON_SLOWDOWN_MANEUVER_TYPES = {"depart", "arrive", "continue", "new name"}
SIGNAL_EXPECTED_DELAY_S = 10.0  # expected value of "sometimes red, sometimes green"
STOP_SIGN_DWELL_S = 3.0
CONTROL_POINT_MAX_OFFSET_M = 30.0  # ignore signals/stops this far from the route (different street)
DEDUPE_DISTANCE_M = 40.0  # merge matches this close together — same intersection, multiple signal poles


def _http_get_json(url, timeout_s=10):
    result = subprocess.run(
        ["curl", "-sS", "-m", str(timeout_s), "-H", f"User-Agent: {USER_AGENT}", url],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl request failed (exit {result.returncode}): {result.stderr.strip()}")
    return json.loads(result.stdout)


def _http_post_json(url, data_field, timeout_s=20):
    result = subprocess.run(
        ["curl", "-sS", "-m", str(timeout_s), "-H", f"User-Agent: {USER_AGENT}",
         "--data-urlencode", f"data={data_field}", url],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl request failed (exit {result.returncode}): {result.stderr.strip()}")
    return json.loads(result.stdout)


def geocode(address):
    """Returns (lat, lon, display_name) for a free-text address, or raises ValueError."""
    query = urllib.parse.quote(address)
    url = f"{NOMINATIM_URL}?q={query}&format=json&limit=1"
    results = _http_get_json(url)
    if not results:
        raise ValueError(f"could not geocode address: {address!r}")
    r = results[0]
    return float(r["lat"]), float(r["lon"]), r["display_name"]


def fetch_route(origin_latlon, dest_latlon):
    """Returns {'distance_m', 'duration_s'} for the driving route between two (lat, lon) points."""
    detailed = fetch_route_detailed(origin_latlon, dest_latlon)
    return {"distance_m": detailed["distance_m"], "duration_s": detailed["duration_s"]}


def fetch_route_detailed(origin_latlon, dest_latlon):
    """Returns {'distance_m', 'duration_s', 'steps', 'geometry'} — steps are OSRM's
    real turn-by-turn segments, geometry is a list of (lon, lat) points along the route."""
    lat1, lon1 = origin_latlon[0], origin_latlon[1]
    lat2, lon2 = dest_latlon[0], dest_latlon[1]
    url = f"{OSRM_URL}/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson&steps=true"
    data = _http_get_json(url)
    if data.get("code") != "Ok":
        raise RuntimeError(f"OSRM routing failed: {data.get('code')} — {data.get('message', '')}")
    route = data["routes"][0]
    return {
        "distance_m": route["distance"],
        "duration_s": route["duration"],
        "steps": route["legs"][0]["steps"],
        "geometry": route["geometry"]["coordinates"],  # [(lon, lat), ...]
    }


def classify_style(distance_m, duration_s):
    """Derives a city/highway/mixed label from OSRM's real average speed — for
    reporting only; the segment-based cycle builder below doesn't need this label."""
    if duration_s <= 0:
        return "mixed"
    avg_kph = (distance_m / 1000.0) / (duration_s / 3600.0)
    if avg_kph >= 65:
        return "highway"
    if avg_kph <= 30:
        return "city"
    return "mixed"


def fetch_traffic_control_points(geometry_lonlat):
    """
    Queries Overpass for traffic_signals/stop nodes within the route's
    bounding box (padded slightly). Returns [(lat, lon, kind), ...].
    """
    lons = [p[0] for p in geometry_lonlat]
    lats = [p[1] for p in geometry_lonlat]
    pad = 0.002  # ~200m, enough to catch nodes right at the bbox edge
    south, west = min(lats) - pad, min(lons) - pad
    north, east = max(lats) + pad, max(lons) + pad

    query = (
        f'[out:json][timeout:25];'
        f'(node["highway"="traffic_signals"]({south},{west},{north},{east});'
        f'node["highway"="stop"]({south},{west},{north},{east}););'
        f"out body;"
    )
    data = _http_post_json(OVERPASS_URL, query)
    points = []
    for element in data.get("elements", []):
        kind = "signal" if element.get("tags", {}).get("highway") == "traffic_signals" else "stop"
        points.append((element["lat"], element["lon"], kind))
    return points


def _haversine_m(lat1, lon1, lat2, lon2):
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _cumulative_distances_m(geometry_lonlat):
    distances = [0.0]
    for i in range(1, len(geometry_lonlat)):
        lon1, lat1 = geometry_lonlat[i - 1]
        lon2, lat2 = geometry_lonlat[i]
        distances.append(distances[-1] + _haversine_m(lat1, lon1, lat2, lon2))
    return distances


def _match_control_points_to_route(control_points, geometry_lonlat, cum_distances_m):
    """Returns sorted, deduplicated [(distance_along_route_m, kind), ...], dropping points too far from the route."""
    matched = []
    for lat, lon, kind in control_points:
        best_dist_m, best_cum_m = float("inf"), None
        for (glon, glat), cum_m in zip(geometry_lonlat, cum_distances_m):
            d = _haversine_m(lat, lon, glat, glon)
            if d < best_dist_m:
                best_dist_m, best_cum_m = d, cum_m
        if best_dist_m <= CONTROL_POINT_MAX_OFFSET_M:
            matched.append((best_cum_m, kind))
    matched.sort(key=lambda pair: pair[0])
    return _dedupe_nearby_events(matched)


def _dedupe_nearby_events(matched):
    """
    A single real intersection is often tagged as several separate OSM nodes
    (one traffic-signal pole per approach), which would otherwise be counted
    as several separate stops a few meters apart. Merge anything within
    DEDUPE_DISTANCE_M of the previous kept event into one stop.
    """
    deduped = []
    for distance_m, kind in matched:
        if deduped and distance_m - deduped[-1][0] < DEDUPE_DISTANCE_M:
            continue
        deduped.append((distance_m, kind))
    return deduped


def _step_needs_slowdown(step):
    return step.get("maneuver", {}).get("type") not in NON_SLOWDOWN_MANEUVER_TYPES


def _build_segments_from_steps(steps):
    """
    Returns [(duration_s, dist_start_m, dist_end_m, speed_start_mps, speed_end_mps), ...]
    — the real route's turn-by-turn profile, before any traffic-control stops
    are spliced in. Each step becomes a transition (turn slowdown, or a smooth
    ramp) followed by a hold at that step's own real average speed.

    Transition segments are given zero distance *width* (dist_start ==
    dist_end) for simplicity — but the vehicle still physically covers real
    distance while ramping speed, and that distance is subtracted from the
    following hold segment's duration (not just left implicit), so each
    step's segments still sum to exactly that step's real distance. Skipping
    this bookkeeping was a real bug caught by comparing the built cycle's
    own integrated distance against the route's real distance — 13 steps'
    worth of "free" transition distance overstated the total by ~2km on a
    ~10km test route.
    """
    segments = []
    prev_speed = 0.0
    cum_d = 0.0

    for i, step in enumerate(steps):
        distance_m, duration_s = step["distance"], step["duration"]
        if distance_m <= 0 or duration_s <= 0:
            continue
        cruise_speed = distance_m / duration_s
        transition_dist = 0.0

        if i == 0:
            accel_t = cruise_speed / ACCEL_MPS2
            transition_dist = 0.5 * cruise_speed * accel_t
            segments.append((accel_t, cum_d, cum_d, prev_speed, cruise_speed))
        elif _step_needs_slowdown(step):
            turn_speed = min(prev_speed, TURN_SPEED_MPS, cruise_speed if cruise_speed > 0 else prev_speed)
            decel_t = max(0.0, (prev_speed - turn_speed) / DECEL_MPS2)
            accel_t = max(0.0, (cruise_speed - turn_speed) / ACCEL_MPS2)
            transition_dist = 0.5 * (prev_speed + turn_speed) * decel_t + 0.5 * (turn_speed + cruise_speed) * accel_t
            segments.append((decel_t, cum_d, cum_d, prev_speed, turn_speed))
            segments.append((accel_t, cum_d, cum_d, turn_speed, cruise_speed))
        else:
            ramp_rate = ACCEL_MPS2 if cruise_speed > prev_speed else DECEL_MPS2
            ramp_t = abs(cruise_speed - prev_speed) / ramp_rate
            transition_dist = 0.5 * (prev_speed + cruise_speed) * ramp_t
            segments.append((ramp_t, cum_d, cum_d, prev_speed, cruise_speed))

        hold_dist = max(0.0, distance_m - transition_dist)
        hold_t = hold_dist / cruise_speed if cruise_speed > 1e-6 else 0.0
        segments.append((hold_t, cum_d, cum_d + distance_m, cruise_speed, cruise_speed))
        cum_d += distance_m
        prev_speed = cruise_speed

    final_decel_t = prev_speed / DECEL_MPS2
    segments.append((final_decel_t, cum_d, cum_d, prev_speed, 0.0))
    return segments


def _splice_in_stops(segments, control_events):
    """
    control_events: sorted [(distance_along_route_m, kind), ...]. Walks the
    segment list and each sorted event together as a single linear merge
    (both are already in route order), splitting whichever segment spans an
    event's distance and inserting a decelerate/dwell/accelerate stop there.

    A stop costs TIME, not extra DISTANCE, relative to the real road — the
    distance covered while decelerating-to-0 and re-accelerating counts
    *toward* the segment's remaining real distance, not on top of it, so the
    spliced cycle's total distance still matches the real route. (Control
    events only ever land in a "hold at cruise speed" segment — the
    transition/ramp segments between steps have zero distance width by
    construction — so speed is exactly constant across the relevant span,
    no approximation needed here.)
    """
    events = list(control_events)
    event_idx = 0
    points = [(0.0, 0.0)]
    t = 0.0

    for duration_s, d0, d1, speed_start, speed_end in segments:
        seg_events = []
        while event_idx < len(events) and d0 <= events[event_idx][0] < d1:
            seg_events.append(events[event_idx])
            event_idx += 1

        if not seg_events:
            t += duration_s
            points.append((t, speed_end))
            continue

        cruise_speed = speed_start  # constant across this segment (see docstring)
        position = d0
        for event_d, kind in seg_events:
            event_d = max(position, min(d1, event_d))
            if cruise_speed > 1e-6:
                t += (event_d - position) / cruise_speed
            points.append((t, cruise_speed))

            decel_t = cruise_speed / DECEL_MPS2
            decel_dist = 0.5 * cruise_speed * decel_t
            t += decel_t
            points.append((t, 0.0))

            dwell_s = SIGNAL_EXPECTED_DELAY_S if kind == "signal" else STOP_SIGN_DWELL_S
            t += dwell_s
            points.append((t, 0.0))

            accel_t = cruise_speed / ACCEL_MPS2
            accel_dist = 0.5 * cruise_speed * accel_t
            t += accel_t
            points.append((t, cruise_speed))

            position = min(d1, event_d + decel_dist + accel_dist)

        remaining_dist = d1 - position
        if remaining_dist > 0 and cruise_speed > 1e-6:
            t += remaining_dist / cruise_speed
        points.append((t, speed_end))

    return points


def build_drive_cycle_from_route(route_detail, include_traffic_controls=True):
    """
    Builds a DriveCycle directly from a real route's turn-by-turn steps
    (and, if requested, real traffic-signal/stop-sign locations along it) —
    not a generic style-block guess.
    """
    segments = _build_segments_from_steps(route_detail["steps"])

    events = []
    if include_traffic_controls:
        try:
            control_points = fetch_traffic_control_points(route_detail["geometry"])
            cum_distances = _cumulative_distances_m(route_detail["geometry"])
            events = _match_control_points_to_route(control_points, route_detail["geometry"], cum_distances)
        except (RuntimeError, ValueError, KeyError) as e:
            # Overpass is a shared public service and can time out or rate-limit;
            # degrade to the segment-only cycle rather than failing the whole trip.
            print(f"warning: traffic-control lookup failed ({e}); continuing without it")

    points = _splice_in_stops(segments, events)
    return DriveCycle(points), len(events)


def build_drive_cycle_from_addresses(origin_address, dest_address, include_traffic_controls=True):
    """
    Geocodes both addresses, fetches a real route between them (with real
    turn-by-turn segments and, by default, real traffic-signal/stop-sign
    locations), and builds a drive cycle directly from it. Returns
    (DriveCycle, route_distance_m, route_info).
    """
    origin_lat, origin_lon, origin_name = geocode(origin_address)
    time.sleep(1.0)  # Nominatim usage policy: max 1 request/second
    dest_lat, dest_lon, dest_name = geocode(dest_address)

    route = fetch_route_detailed((origin_lat, origin_lon), (dest_lat, dest_lon))
    cycle, num_control_points = build_drive_cycle_from_route(route, include_traffic_controls)

    route_info = {
        "origin_name": origin_name,
        "origin_lat": origin_lat,
        "origin_lon": origin_lon,
        "dest_name": dest_name,
        "style": classify_style(route["distance_m"], route["duration_s"]),
        "route_distance_m": route["distance_m"],
        "route_duration_s": route["duration_s"],
        "num_steps": len(route["steps"]),
        "num_traffic_controls": num_control_points,
    }
    return cycle, route["distance_m"], route_info
