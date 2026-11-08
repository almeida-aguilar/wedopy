"""Transport abstraction (spec 12.1). Synchronous: backends hide their own event loops.

Contract:

* every method that talks to the hub takes a ``timeout`` in seconds and raises
  ``OperationTimeout`` / ``BLEError`` / ``HubDisconnectedError`` (``wedopy`` exceptions);
* writes are always *with response*; a backend must not silently fall back to
  write-without-response, because that would remove the ACK the watchdog relies on;
* notification callbacks may run on a backend thread and must not block.
"""
import abc


class Transport(abc.ABC):
    @abc.abstractmethod
    def set_callbacks(self, on_notify, on_disconnect):
        """``on_notify(char_uuid, data)`` and ``on_disconnect(reason)``; UUIDs are canonical 128-bit."""

    @abc.abstractmethod
    def connect(self, timeout):
        """Scan for the first WeDo 2.0 hub, connect and discover its services."""

    @abc.abstractmethod
    def disconnect(self, timeout=None):
        """Close the link. Must be safe to call when not connected."""

    @abc.abstractmethod
    def has_characteristic(self, uuid):
        """True when the connected device exposes the characteristic."""

    @abc.abstractmethod
    def read(self, uuid, timeout):
        """Read a characteristic with response."""

    @abc.abstractmethod
    def write(self, uuid, data, timeout):
        """Write a characteristic with response; return only after the hub ACKs."""

    @abc.abstractmethod
    def subscribe(self, uuid, timeout):
        """Enable notifications."""

    @abc.abstractmethod
    def unsubscribe(self, uuid, timeout):
        """Disable notifications."""
