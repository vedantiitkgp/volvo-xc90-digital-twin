"""
Run a real point-A-to-point-B trip: geocodes both addresses (Nominatim) and
fetches an actual driving route between them (OSRM), then builds a drive
cycle from the route's real distance and a style classified from its real
average speed — see xc90_sim.trip.live_routing for exactly what this does
and doesn't model (still no turn-by-turn speed profile from the route
geometry itself, just distance + an average-speed-derived style).

Requires internet access and `curl` on PATH. Uses free public services
(OpenStreetMap Nominatim + the OSRM demo server) meant for light use.

Usage: python3 examples/run_real_trip.py "<origin address>" "<destination address>"
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xc90_sim.trip import build_drive_cycle_from_addresses, run_drive_cycle
from run_trip import print_report


def main():
    if len(sys.argv) < 3:
        print(f"Usage: python3 {sys.argv[0]} \"<origin address>\" \"<destination address>\"")
        sys.exit(1)

    origin_address, dest_address = sys.argv[1], sys.argv[2]
    cycle, _, route_info = build_drive_cycle_from_addresses(origin_address, dest_address)

    print(f"Route: {route_info['origin_name']}")
    print(f"    -> {route_info['dest_name']}")
    print(f"  {route_info['route_distance_m']/1000:.2f} km, "
          f"OSRM estimate {route_info['route_duration_s']/60:.1f} min, "
          f"classified as '{route_info['style']}'")
    print(f"  {route_info['num_steps']} real turn-by-turn segments, "
          f"{route_info['num_traffic_controls']} traffic signals/stop signs along the route")
    print()

    report = run_drive_cycle(cycle, origin_latlon=(route_info["origin_lat"], route_info["origin_lon"]))
    print_report(report, route_info["style"], route_info["route_distance_m"] / 1000.0)


if __name__ == "__main__":
    main()
