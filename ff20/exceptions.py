class FF20Error(Exception):
    """Base exception for user-facing FF20 errors."""


class DeviceNotFoundError(FF20Error):
    """No FF20 pedal was detected."""


class DeviceBusyError(FF20Error):
    """The FF20 appears to be busy or already open by another application."""


class CommunicationError(FF20Error):
    """USB/HID communication with the FF20 failed."""


class InvalidSlotError(FF20Error):
    """The requested loop slot is invalid."""
