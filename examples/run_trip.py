"""
Run a synthetic point-A-to-point-B trip and report how much each component
was used over the drive — gear time, rpm bands, throttle bands, converter
lockup %, AWD front/rear split, brake usage, peak g's.

No live routing/map API is available here, so "point A to point B" is
represented as (distance_km, style) rather than real addresses — see
xc90_sim.trip.drive_cycle for what that does and doesn't model.

Usage: python3 examples/run_trip.py [distance_km] [city|highway|mixed]
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xc90_sim.trip import build_drive_cycle, run_drive_cycle


def run_trip(distance_km, style):
    cycle, actual_distance_m = build_drive_cycle(distance_km, style)
    report = run_drive_cycle(cycle)
    return report, cycle


def print_report(report, style, requested_km):
    print(f"Trip: {requested_km} km requested ({style}), {report['distance_km']:.2f} km actually driven")
    print(f"  Elapsed: {report['elapsed_s']/60:.1f} min, avg speed {report['avg_speed_kph']:.1f} kph")
    print()
    print("  Gear usage:")
    for gear, pct in report["gear_pct"].items():
        print(f"    gear {gear}: {pct:5.1f}%")
    print()
    print("  Engine RPM band usage:")
    for label, pct in report["rpm_band_pct"].items():
        print(f"    {label:20s}: {pct:5.1f}%")
    print()
    print("  Throttle band usage:")
    for label, pct in report["throttle_band_pct"].items():
        print(f"    {label:20s}: {pct:5.1f}%")
    print()
    print(f"  Torque converter locked: {report['converter_locked_pct']:.1f}% of trip")
    print(f"  Manual shift mode:       {report['manual_mode_pct']:.1f}% of trip")
    print(f"  Brakes actively applied: {report['brake_active_pct']:.1f}% of trip")
    print(f"  Avg Haldex front bias:   {report['avg_awd_front_bias_pct']:.1f}% front")
    print(f"  Peak lateral g:          {report['max_lateral_g']:.2f} g")
    print(f"  Peak longitudinal g:     {report['max_longitudinal_g']:.2f} g")


if __name__ == "__main__":
    distance_km = float(sys.argv[1]) if len(sys.argv) > 1 else 15.0
    style = sys.argv[2] if len(sys.argv) > 2 else "mixed"

    report, _ = run_trip(distance_km, style)
    print_report(report, style, distance_km)
