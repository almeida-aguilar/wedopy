"""Exception hierarchy. Canonical definitions live here so the core has no
import dependency on the public package; ``wedopy.exceptions`` re-exports them."""


class WedoError(Exception):
    pass


class BLEError(WedoError, OSError):
    pass


class HubConnectionError(WedoError, ConnectionError):
    pass


class HubDisconnectedError(HubConnectionError):
    pass


class OperationTimeout(WedoError, TimeoutError):
    pass


class HubBusyError(WedoError, RuntimeError):
    pass


class DeviceNotFoundError(WedoError, LookupError):
    pass


class DeviceTypeError(WedoError):
    pass


class AmbiguousDeviceError(WedoError, LookupError):
    pass


class InvalidStateError(WedoError, RuntimeError):
    pass


class UnsupportedFeatureError(WedoError, NotImplementedError):
    pass
