"""Native tools for the Flamma FF20 looper pedal."""

from .pedal import DeviceInfo, FF20Pedal, LoopInfo
from .exceptions import (
    CommunicationError,
    DeviceBusyError,
    DeviceNotFoundError,
    FF20Error,
    InvalidSlotError,
)

__all__ = [
    "FF20Pedal",
    "LoopInfo",
    "DeviceInfo",
    "FF20Error",
    "DeviceNotFoundError",
    "DeviceBusyError",
    "CommunicationError",
    "InvalidSlotError",
]

__version__ = "1.0.0"
