"""Lifecycle of one hub session: coordinator, task manager and supervisor registration."""
import logging

from wedopy_core import _wedopy as _core
from wedopy_core.exceptions import InvalidStateError
from wedopy_core.runtime.supervisor import supervisor

from .tasks import TaskManager

_log = logging.getLogger("wedopy")


class Session:
    def __init__(self, transport=None, timing=None):
        self._transport = transport
        self._timing = timing
        self._core = None
        self.tasks = TaskManager(on_interrupt=self._interrupted)

    # -- access ---------------------------------------------------------------

    @property
    def core(self):
        """The coordinator. Raises if the hub was never connected."""
        if self._core is None:
            raise InvalidStateError("hub is not connected; call connect() first")
        return self._core

    @property
    def is_connected(self):
        return self._core is not None and self._core.state is _core.HubState.CONNECTED

    # -- lifecycle ------------------------------------------------------------

    def connect(self):
        if self._core is None:
            transport = self._transport
            if transport is None:
                from wedopy_core.transport.ble import BleakTransport
                transport = BleakTransport()
            self._core = _core.Coordinator(transport, self._timing)
        self._core.connect()
        supervisor.register(self)

    def disconnect(self):
        """Cancel tasks first (so none can order a motor after the stop), then stop motors and close."""
        self.tasks.cancel()
        if self._core is not None:
            self._core.disconnect()
        supervisor.unregister(self)

    def shutdown(self):
        self.tasks.cancel()
        core = self.core
        try:
            core.stop_all()
        except Exception as exc:
            _log.warning("could not stop motors before shutdown: %r", exc)
        core.shutdown_hub()
        supervisor.unregister(self)

    def stop_all(self):
        self.core.stop_all()

    def ports_raw(self):
        return self._core.ports_raw() if self._core is not None else {}

    def refresh_ports(self):
        self.core.refresh_ports()

    # -- safety hooks -----------------------------------------------------------

    def emergency_close(self):
        """Called by the supervisor at interpreter exit. Best effort, never raises."""
        try:
            self.tasks.cancel()
            if self._core is not None:
                self._core.disconnect()
        except Exception:
            _log.debug("emergency close failed", exc_info=True)

    def _interrupted(self):
        """Ctrl+C during ``tasks.wait()``: try to stop the motors (spec 10.4)."""
        if self.is_connected:
            try:
                self._core.stop_all()
            except Exception as exc:
                _log.warning("could not stop motors after interrupt: %r", exc)
