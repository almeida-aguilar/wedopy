"""Public exceptions. The classes are defined in ``wedopy_core.exceptions`` (so the core does
not depend on this package) and re-exported here."""
from wedopy_core import exceptions as _core

__all__ = [
    "WedoError", "BLEError", "HubConnectionError", "HubDisconnectedError", "OperationTimeout",
    "HubBusyError", "DeviceNotFoundError", "DeviceTypeError", "AmbiguousDeviceError",
    "InvalidStateError", "UnsupportedFeatureError",
]

for _name in __all__:
    _cls = getattr(_core, _name)
    _cls.__module__ = __name__
    globals()[_name] = _cls
del _name, _cls
