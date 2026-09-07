"""
GPS receiver: a real live position fix, not just the destination/distance/
ETA pass-through Infotainment already had. Converts the vehicle's own
real, physics-derived local position (VehicleBody.world_x_m/world_y_m —
genuinely integrated from real wheel forces, not assumed) into a real
lat/lon by projecting around a real-world origin (e.g. a live-routed
trip's actual geocoded start address — see xc90_sim.trip.live_routing).

Uses an equirectangular (flat-Earth) projection, valid for the short
local distances a single car trip covers (a few/tens of km) — this
project's trips are city/commute-length, well within where that
approximation holds; it would drift for a genuinely long (hundreds of km)
trip, which isn't this project's use case.

Real, imperfect sensor characteristics, same "sensors aren't perfect"
philosophy as WheelSpeedSensor/OxygenSensor: real GPS position noise (a
few meters), and a genuine "lost signal" state (tunnels, parking garages,
dense urban canyons) — externally settable, same fault-injection pattern
as Relay/Fuse, since this project doesn't simulate real satellite
geometry/multipath physics.

No origin means no fix at all (honest "GPS searching" state) — matches a
real receiver's cold-start behavior, here simplified to "hasn't been given
a real-world reference point yet" rather than modeling actual satellite
acquisition time.
"""

import math
import random

from ..specs import sensors as specs


class GPS:
    def __init__(self):
        self.origin_lat = None
        self.origin_lon = None
        self.lat = None
        self.lon = None
        self.heading_deg = None
        self.signal_lost = False

    def set_origin(self, lat, lon):
        """Real-world lat/lon corresponding to the vehicle body's local
        (world_x_m, world_y_m) = (0, 0) — e.g. a live-routed trip's actual
        geocoded start address."""
        self.origin_lat = lat
        self.origin_lon = lon

    def set_signal_lost(self, lost):
        self.signal_lost = lost

    def has_fix(self):
        return self.origin_lat is not None and not self.signal_lost

    def step(self, world_x_m, world_y_m, heading_rad):
        if self.origin_lat is None or self.signal_lost:
            return  # no fix -- real receiver in a tunnel/garage holds its last position, doesn't update

        # +X is treated as East, +Y as North -- an arbitrary but consistent
        # convention, since this project doesn't otherwise track a real
        # compass heading at trip start to align to.
        noisy_x_m = world_x_m + random.gauss(0.0, specs.GPS_POSITION_NOISE_STD_M)
        noisy_y_m = world_y_m + random.gauss(0.0, specs.GPS_POSITION_NOISE_STD_M)

        self.lat = self.origin_lat + math.degrees(noisy_y_m / specs.EARTH_RADIUS_M)
        self.lon = self.origin_lon + math.degrees(
            noisy_x_m / (specs.EARTH_RADIUS_M * math.cos(math.radians(self.origin_lat)))
        )
        self.heading_deg = math.degrees(heading_rad) % 360.0
