"""
Infotainment head unit: power/volume/source state, current touchscreen
menu screen, plus a thin pass-through for navigation status (destination/
distance/ETA) — deliberately NOT coupled to xc90_sim.trip.live_routing
internally, so this stays testable standalone; a caller that has a real
route (see trip/) can push its own numbers in here.

Screens mirror the real Sensus touchscreen's menu structure: Climate,
Park Assist, Seats, and Car Status (oil life, tire pressure) are all real
menu pages a driver navigates to, not just backend method calls with no
UI home — see Simulation.infotainment_screen_data(), which aggregates
whichever subsystem's status the current screen needs without coupling
this class itself to HVAC/ParkingAssist/Seating/etc.
"""

SOURCES = ("off", "radio", "bluetooth", "usb", "nav")
SCREENS = ("home", "media", "nav", "climate", "park_assist", "seats", "car_status")


class Infotainment:
    def __init__(self):
        self.power_on = False
        self.volume_pct = 20.0
        self.muted = False
        self.source = "off"
        self.current_screen = "home"
        self.destination = None
        self.distance_remaining_km = None
        self.eta_min = None

    def set_screen(self, screen):
        if screen not in SCREENS:
            raise ValueError(f"unknown infotainment screen: {screen!r}, expected one of {SCREENS}")
        self.current_screen = screen

    def set_power(self, on):
        self.power_on = on
        if not on:
            self.source = "off"

    def set_volume_pct(self, pct):
        self.volume_pct = max(0.0, min(100.0, pct))

    def set_muted(self, muted):
        self.muted = muted

    def set_source(self, source):
        if source not in SOURCES:
            raise ValueError(f"unknown source {source!r}, expected one of {SOURCES}")
        self.source = source

    def set_navigation(self, destination, distance_remaining_km=None, eta_min=None):
        self.destination = destination
        self.distance_remaining_km = distance_remaining_km
        self.eta_min = eta_min
        if self.power_on:
            self.source = "nav"

    def clear_navigation(self):
        self.destination = None
        self.distance_remaining_km = None
        self.eta_min = None
