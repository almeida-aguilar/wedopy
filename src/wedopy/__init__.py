"""wedopy: control the LEGO WeDo 2.0 Smart Hub from Python.

    from wedopy import Hub

    with Hub() as hub:
        motor = hub.motor("A")
        motor.run(100)
"""
from . import task
from .button import Button
from .exceptions import (
    AmbiguousDeviceError,
    BLEError,
    DeviceNotFoundError,
    DeviceTypeError,
    HubBusyError,
    HubConnectionError,
    HubDisconnectedError,
    InvalidStateError,
    OperationTimeout,
    UnsupportedFeatureError,
    WedoError,
)
from .hub import Hub
from .led import LED
from .motor import Motor, MotorGroup
from .sensors import DistanceSensor, TiltSensor
from .time import running_time

__version__ = "0.1.0.dev0"

__all__ = [
    "Hub", "Motor", "MotorGroup", "DistanceSensor", "TiltSensor", "LED", "Button",
    "task", "running_time",
    "WedoError", "BLEError", "HubConnectionError", "HubDisconnectedError", "OperationTimeout",
    "HubBusyError", "DeviceNotFoundError", "DeviceTypeError", "AmbiguousDeviceError",
    "InvalidStateError", "UnsupportedFeatureError",
]
