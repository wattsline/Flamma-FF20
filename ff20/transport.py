from __future__ import annotations

import sys
from typing import Optional

import hid

from .constants import (
    CMD_PAYLOAD_LIMIT,
    CMD_REPORT_SIZE,
    DATA_REPORT_SIZE,
    IFACE_CMD,
    IFACE_DATA,
    PID_APP,
    PID_BOOT,
    VID,
)
from .exceptions import CommunicationError, DeviceNotFoundError


def _path_bytes(value):
    return value if isinstance(value, bytes) else str(value).encode("utf-8")


class HIDTransport:
    """Low-level FF20 HID transport."""

    def __init__(self, serial: Optional[str] = None, verbose: bool = False) -> None:
        self.serial = serial
        self.verbose = verbose
        self.cmd = None
        self.data = None

    @staticmethod
    def all_devices() -> list[dict]:
        return [d for d in hid.enumerate(VID, 0) if d.get("product_id") in (PID_APP, PID_BOOT)]

    @staticmethod
    def app_devices() -> list[dict]:
        return list(hid.enumerate(VID, PID_APP))

    def _debug(self, msg: str) -> None:
        if self.verbose:
            print(f"[ff20] {msg}", file=sys.stderr)

    def _find_paths(self) -> tuple[bytes, bytes]:
        candidates = self.app_devices()
        if self.serial:
            candidates = [d for d in candidates if d.get("serial_number") == self.serial]

        if not candidates:
            raise DeviceNotFoundError(
                "No FF20 pedal was detected.\n\n"
                "Please check:\n"
                "  • USB cable is connected\n"
                "  • Pedal is powered on\n"
                "  • The official Flamma application is closed"
            )

        cmd_path = None
        data_path = None

        for d in candidates:
            iface = d.get("interface_number")
            path = d.get("path")
            if path is None:
                continue
            if iface == IFACE_CMD:
                cmd_path = path
                self.serial = d.get("serial_number") or self.serial
            elif iface == IFACE_DATA:
                data_path = path

        if cmd_path is None or data_path is None:
            raise DeviceNotFoundError(
                "The FF20 was detected, but its required USB interfaces are incomplete.\n\n"
                "Try unplugging/replugging the pedal and closing the official Flamma app."
            )

        return _path_bytes(cmd_path), _path_bytes(data_path)

    def open(self) -> "HIDTransport":
        cmd_path, data_path = self._find_paths()
        try:
            self.cmd = hid.Device(path=cmd_path)
            self.data = hid.Device(path=data_path)
        except Exception as exc:
            raise CommunicationError(f"Unable to open FF20 HID interfaces: {exc}") from exc

        try:
            self.cmd.nonblocking = False
            self.data.nonblocking = False
        except Exception:
            pass

        return self

    def close(self) -> None:
        for dev in (self.cmd, self.data):
            if dev is not None:
                try:
                    dev.close()
                except Exception:
                    pass

    def __enter__(self) -> "HIDTransport":
        return self.open()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def write_command_bytes(self, data: bytes) -> None:
        if self.cmd is None:
            raise CommunicationError("Transport is not open")

        try:
            for off in range(0, len(data), CMD_PAYLOAD_LIMIT):
                chunk = data[off:off + CMD_PAYLOAD_LIMIT]
                report = bytes([CMD_PAYLOAD_LIMIT]) + chunk + bytes(CMD_REPORT_SIZE - 1 - len(chunk))
                self._debug(f"cmd write {report.hex(' ')}")
                self.cmd.write(report)
        except Exception as exc:
            raise CommunicationError(f"Command write failed: {exc}") from exc

    def read_command_report(self, timeout_ms: int = 3000) -> bytes:
        if self.cmd is None:
            raise CommunicationError("Transport is not open")
        try:
            report = self.cmd.read(CMD_REPORT_SIZE, timeout_ms)
        except Exception as exc:
            raise CommunicationError(f"Command read failed: {exc}") from exc

        if not report:
            raise CommunicationError("Timed out waiting for command response")

        data = bytes(report)
        self._debug(f"cmd read {data.hex(' ')}")
        return data

    def write_data_bytes(self, data: bytes) -> None:
        if self.data is None:
            raise CommunicationError("Transport is not open")

        try:
            for off in range(0, len(data), DATA_REPORT_SIZE):
                chunk = data[off:off + DATA_REPORT_SIZE]
                report = chunk + bytes(DATA_REPORT_SIZE - len(chunk))
                # Required by macOS/node-hid behavior for FF20 interface 1.
                report_to_send = bytes([0]) + report
                self._debug(f"data write len={len(report_to_send)}")
                self.data.write(report_to_send)
        except Exception as exc:
            raise CommunicationError(f"Data write failed: {exc}") from exc

    def read_data_report(self, timeout_ms: int = 3000) -> bytes:
        if self.data is None:
            raise CommunicationError("Transport is not open")
        try:
            report = self.data.read(DATA_REPORT_SIZE, timeout_ms)
        except Exception as exc:
            raise CommunicationError(f"Data read failed: {exc}") from exc

        if not report:
            raise CommunicationError("Timed out waiting for data response")

        data = bytes(report)
        self._debug(f"data read len={len(data)}")
        return data
