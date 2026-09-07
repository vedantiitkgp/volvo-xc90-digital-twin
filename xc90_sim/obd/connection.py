"""
Thin wrapper around python-OBD's connection, supporting both USB and WiFi
ELM327 adapters through the same `portstr` — python-OBD opens the port via
pyserial's `serial_for_url()`, which understands the `socket://host:port`
URL scheme natively, so a WiFi adapter needs no special-casing:

    OBDConnection()                                # USB, auto-detect port
    OBDConnection(port="/dev/tty.usbserial-1420")  # USB, explicit port
    OBDConnection(port="COM3")                     # USB, Windows
    OBDConnection(port="socket://192.168.0.10:35000")  # WiFi, ELM327's usual default

UNTESTED against real hardware — this was written and reviewed for
correctness against python-OBD's documented API, but there was no physical
ELM327 adapter or car available to verify it against. Expect to debug the
actual port/IP for your specific adapter.
"""

import obd


class OBDConnection:
    def __init__(self, port=None, fast=True):
        self.connection = obd.OBD(portstr=port, fast=fast)

    def is_connected(self):
        return self.connection.is_connected()

    def query(self, command_name):
        """command_name: an attribute name on obd.commands, e.g. 'RPM', 'SPEED'.
        Returns the response's magnitude (a plain float/int) or None if
        unsupported/no data."""
        command = getattr(obd.commands, command_name)
        response = self.connection.query(command)
        if response.is_null():
            return None
        value = response.value
        return value.magnitude if hasattr(value, "magnitude") else value

    def supports(self, command_name):
        command = getattr(obd.commands, command_name)
        return self.connection.supports(command)

    def close(self):
        self.connection.close()
