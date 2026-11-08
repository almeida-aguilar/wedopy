"""BLE backend built on ``bleak`` (BlueZ on Linux first; spec 12.1).

bleak is asyncio-based, so this backend owns a private event loop on a daemon thread and
exposes the synchronous :class:`Transport` interface. The user never sees asyncio.

NOT validated on real hardware yet.
"""
import asyncio
import concurrent.futures
import threading

from wedopy_core.exceptions import (
    BLEError,
    HubConnectionError,
    HubDisconnectedError,
    OperationTimeout,
    WedoError,
)
from wedopy_core.protocol import constants as K
from wedopy_core.protocol.uuid import normalize_uuid
from .interfaces import Transport

_WEDO_NAMES = ("LPF2 Smart Hub 2 I/O",)


class BleakTransport(Transport):
    def __init__(self, address=None):
        """``address``: optional BLE address to connect to instead of scanning for the first hub."""
        try:
            import bleak  # noqa: F401
        except ImportError as exc:  # pragma: no cover
            raise BLEError("the BLE backend needs the 'bleak' package: pip install bleak") from exc
        self._address = address
        self._loop = None
        self._thread = None
        self._client = None
        self._chars = set()
        self._on_notify = None
        self._on_disconnect = None
        self._closing = False

    # -- plumbing ---------------------------------------------------------

    def set_callbacks(self, on_notify, on_disconnect):
        self._on_notify = on_notify
        self._on_disconnect = on_disconnect

    def _ensure_loop(self):
        if self._loop is not None:
            return
        loop = asyncio.new_event_loop()
        ready = threading.Event()

        def run():
            asyncio.set_event_loop(loop)
            loop.call_soon(ready.set)
            loop.run_forever()

        self._thread = threading.Thread(target=run, name="wedopy-bleak", daemon=True)
        self._thread.start()
        ready.wait(5.0)
        self._loop = loop

    def _stop_loop(self):
        loop, thread = self._loop, self._thread
        self._loop = self._thread = None
        if loop is not None:
            loop.call_soon_threadsafe(loop.stop)
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)

    def _run(self, coro, timeout):
        if self._loop is None:
            coro.close()
            raise HubDisconnectedError("BLE link is not open")
        fut = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            return fut.result(timeout)
        except concurrent.futures.TimeoutError:
            fut.cancel()
            raise OperationTimeout("BLE operation timed out after %.1f s" % timeout) from None
        except WedoError:
            raise
        except Exception as exc:
            if self._client is not None and not self._client.is_connected:
                raise HubDisconnectedError(str(exc) or "BLE link lost") from exc
            raise BLEError(str(exc) or exc.__class__.__name__) from exc

    def _require_link(self):
        if self._client is None or not self._client.is_connected:
            raise HubDisconnectedError("BLE link is not open")

    # -- Transport --------------------------------------------------------

    def connect(self, timeout):
        from bleak import BleakClient, BleakScanner

        self._ensure_loop()
        self._closing = False

        def is_wedo(device, adv):
            uuids = [u.lower() for u in (adv.service_uuids or [])]
            return K.SERVICE_HUB in uuids or (adv.local_name or device.name or "") in _WEDO_NAMES

        async def go():
            if self._address:
                target = await BleakScanner.find_device_by_address(self._address, timeout=timeout / 2)
            else:
                target = await BleakScanner.find_device_by_filter(is_wedo, timeout=timeout / 2)
            if target is None:
                raise HubConnectionError("no WeDo 2.0 hub found; is it on and in range?")
            client = BleakClient(target, disconnected_callback=self._disconnected)
            await client.connect()
            self._client = client
            self._chars = {c.uuid.lower() for s in client.services for c in s.characteristics}

        self._run(go(), timeout)

    def _disconnected(self, _client):
        if self._closing:
            return
        cb = self._on_disconnect
        if cb is not None:
            cb("BLE link lost")

    def disconnect(self, timeout=None):
        client = self._client
        self._closing = True
        self._client = None
        self._chars = set()
        if client is not None and self._loop is not None:
            try:
                self._run(client.disconnect(), timeout or 5.0)
            except WedoError:
                pass
        self._stop_loop()

    def has_characteristic(self, uuid):
        return normalize_uuid(uuid) in self._chars

    def read(self, uuid, timeout):
        self._require_link()
        return bytes(self._run(self._client.read_gatt_char(uuid), timeout))

    def write(self, uuid, data, timeout):
        self._require_link()
        # Always with response: the ACK is what the watchdog relies on (spec 10.2).
        self._run(self._client.write_gatt_char(uuid, bytes(data), response=True), timeout)

    def subscribe(self, uuid, timeout):
        self._require_link()
        key = normalize_uuid(uuid)

        def handler(_sender, data):
            cb = self._on_notify
            if cb is not None:
                cb(key, bytes(data))

        self._run(self._client.start_notify(uuid, handler), timeout)

    def unsubscribe(self, uuid, timeout):
        self._require_link()
        self._run(self._client.stop_notify(uuid), timeout)
