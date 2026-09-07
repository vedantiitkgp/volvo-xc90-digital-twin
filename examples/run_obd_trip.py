"""
Log a REAL trip from your actual car's OBD2 port, through the same
CAN-bus/trip-logger framework the simulator uses for synthetic and
live-routed trips — see xc90_sim/obd/ for exactly what data this can and
can't get from a generic (non-manufacturer-specific) OBD2 connection.

UNTESTED against real hardware — written and reviewed against python-OBD's
documented API, but there was no physical ELM327 adapter or car available
to verify against. You'll likely need to adjust the port/IP below for your
specific adapter; see the troubleshooting notes at the bottom of this file.

Requires: pip install obd

Usage:
  python3 examples/run_obd_trip.py                          # USB, auto-detect port
  python3 examples/run_obd_trip.py /dev/tty.usbserial-1420   # USB, explicit port (macOS/Linux)
  python3 examples/run_obd_trip.py COM3                      # USB, explicit port (Windows)
  python3 examples/run_obd_trip.py socket://192.168.0.10:35000  # WiFi ELM327
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from xc90_sim.network import CANBus
from xc90_sim.obd import OBDConnection, OBD2Bridge
from xc90_sim.trip import TripLogger
from run_trip import print_report


def main():
    port = sys.argv[1] if len(sys.argv) > 1 else None

    print("Connecting to OBD2 adapter" + (f" at {port}" if port else " (auto-detecting port)") + "...")
    connection = OBDConnection(port=port)
    if not connection.is_connected():
        print("Failed to connect. Check that the adapter is plugged in, paired (if Bluetooth-"
              "bridged), and that the port/IP above is correct for your specific adapter.")
        sys.exit(1)
    print("Connected. Logging trip — press Ctrl+C to stop and print the report.\n")

    bus = CANBus()
    logger = TripLogger(bus)
    bridge = OBD2Bridge(connection, bus, poll_period_s=0.5)

    distance_km_estimate = 0.0
    elapsed_s = 0.0
    try:
        bridge.run()  # runs until Ctrl+C
    except KeyboardInterrupt:
        pass
    finally:
        connection.close()

    # This bridge doesn't track odometer distance itself (no dedicated PID
    # polled for it here) — report elapsed time and whatever CAN-derived
    # stats were captured; pass 0 for distance if you don't have a better estimate.
    report = logger.report(distance_km_estimate * 1000.0, logger.total_time_s)
    print_report(report, "real (OBD2)", distance_km_estimate)


if __name__ == "__main__":
    main()

# --- Troubleshooting notes (untested — best-effort guidance) ---
#
# USB adapter not found / auto-detect fails:
#   macOS: check `ls /dev/tty.*` for something like /dev/tty.usbserial-XXXX
#     or /dev/tty.SLAB_USBtoUART, pass it explicitly.
#   Windows: check Device Manager > Ports (COM & LPT) for the assigned COM port.
#   Linux: check `ls /dev/ttyUSB*` or `/dev/ttyACM*`.
#
# WiFi adapter: most ELM327 WiFi dongles create their own WiFi network you
#   must join first (commonly SSID "WiFi_OBDII", password "12345678"), and
#   default to IP 192.168.0.10 port 35000 — but this varies by adapter
#   brand, check its manual. Once joined, use socket://<ip>:<port>.
#
# Bluetooth: not directly supported by this script — python-OBD expects a
#   serial port, so a Bluetooth ELM327 needs to be paired at the OS level
#   first (which exposes it as a virtual serial port), then used like USB.
#
# "No OBD-II adapters found": the car's ignition may need to be ON (engine
#   running or accessory mode) for the OBD2 port to be powered/respond.
