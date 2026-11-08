# cython: language_level=3, binding=True
"""wedopy native core (private module ``wedopy_core._wedopy``).

Contains:

* protocol codecs (encoders/decoders, checked against the captured vectors),
* the explicit hub state machine,
* the single-writer :class:`Coordinator` (normal + emergency queues),
* heartbeat and watchdog threads, independent of the user's task scheduler.

The source is deliberately written in the subset of Cython that is also valid
Python, so the same file can be compiled by Cython or run uncompiled in tests.
Typed ``cdef`` optimisations can be layered on later, after measuring.
"""
import collections
import enum
import logging
import math
import struct
import threading
import time

from wedopy_core.exceptions import (
    BLEError,
    DeviceNotFoundError,
    DeviceTypeError,
    HubBusyError,
    HubConnectionError,
    HubDisconnectedError,
    InvalidStateError,
    OperationTimeout,
    WedoError,
)
from wedopy_core.protocol import constants as K
from wedopy_core.runtime.timing import Timing

_log = logging.getLogger("wedopy")
_wlog = logging.getLogger("wedopy.watchdog")

# ---------------------------------------------------------------------------
# Protocol codecs
# ---------------------------------------------------------------------------

PortEvent = collections.namedtuple("PortEvent", "conn attached hub_index type")
Sample = collections.namedtuple("Sample", "conn value raw")

TILT_DIRECTIONS = {0: "neutral", 3: "back", 5: "right", 7: "left", 9: "forward"}


def motor_power(conn, speed):
    """Output command: ``[conn, 01, 01, int8(speed)]``. Speed is clamped to -100..100."""
    if speed > 100:
        speed = 100
    if speed < -100:
        speed = -100
    return bytes((conn, 0x01, 0x01, speed & 0xFF))


def led_index(index):
    """Predefined colour (LED must be in discrete mode)."""
    return bytes((K.CONN_RGB, 0x04, 0x01, index))


def led_rgb(r, g, b):
    """Absolute colour (LED must be in absolute mode)."""
    return bytes((K.CONN_RGB, 0x04, 0x03, r, g, b))


def input_format(conn, typ, mode, delta, unit, notify):
    """Input command ``[01 02 conn type mode delta(4, LE) unit notify]``."""
    return struct.pack("<BBBBBIBB", 0x01, 0x02, conn, typ, mode, delta, unit, 1 if notify else 0)


def input_start(conn):
    """The "start sensor working" signal seen in the captures."""
    return bytes((0x00, 0x01, conn))


def parse_port_event(data):
    """Decode ``[conn 00]`` (detach) or ``[conn 01 hub_index type ...]`` (attach)."""
    if len(data) < 2:
        raise ValueError("port event too short (%d bytes)" % len(data))
    conn = data[0]
    attached = data[1] == 1
    if not attached:
        return PortEvent(conn, False, 0, 0)
    if len(data) < 4:
        raise ValueError("attach event too short (%d bytes)" % len(data))
    return PortEvent(conn, True, data[2], data[3])


def parse_sample(data):
    """Decode a Sensor Value notification ``[?, conn, value...]``.

    The first byte is undocumented and kept uninterpreted (spec 12.2).
    """
    if len(data) < 2:
        raise ValueError("sensor value too short (%d bytes)" % len(data))
    raw = bytes(data)
    return Sample(raw[1], raw[2:], raw)


def decode_scalar(value):
    """1 byte = uint8, 2 = uint16 LE, 4 = float32 LE."""
    n = len(value)
    if n == 1:
        return float(value[0])
    if n == 2:
        return float(struct.unpack("<H", value)[0])
    if n == 4:
        return float(struct.unpack("<f", value)[0])
    raise ValueError("cannot decode a %d-byte sensor value" % n)


def decode_tilt_angle(value):
    """Angle mode: two float32 (SI, 8 bytes) or two int8. Returns rounded ints (x, y)."""
    if len(value) == 8:
        x, y = struct.unpack("<ff", value)
        if not (math.isfinite(x) and math.isfinite(y)):
            raise ValueError("non-finite tilt angle")
        return int(round(x)), int(round(y))
    if len(value) < 2:
        raise ValueError("tilt angle value too short (%d bytes)" % len(value))
    return struct.unpack("<bb", value[:2])


def tilt_direction_name(value):
    """Direction mode code -> name (verified on hardware, nov 2026)."""
    code = decode_scalar(value)
    if not math.isfinite(code):
        return "unknown"
    return TILT_DIRECTIONS.get(int(code), "unknown")


def hex_string(data):
    return " ".join("%02x" % b for b in data)


# ---------------------------------------------------------------------------
# State machine
# ---------------------------------------------------------------------------


class HubState(enum.Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    SHUTDOWN = "shutdown"
    ERROR = "error"


_S = HubState
_TRANSITIONS = {
    _S.DISCONNECTED: {_S.CONNECTING},
    _S.CONNECTING: {_S.CONNECTED, _S.ERROR, _S.DISCONNECTED},
    _S.CONNECTED: {_S.DISCONNECTING, _S.ERROR, _S.SHUTDOWN},
    _S.DISCONNECTING: {_S.DISCONNECTED, _S.ERROR},
    _S.SHUTDOWN: {_S.CONNECTING, _S.DISCONNECTED},
    _S.ERROR: {_S.CONNECTING, _S.DISCONNECTING, _S.DISCONNECTED},
}


# ---------------------------------------------------------------------------
# Coordinator
# ---------------------------------------------------------------------------


class _Request:
    """One unit of work for the single BLE writer thread."""

    def __init__(self, fn, emergency, needs_connected):
        self.fn = fn
        self.emergency = emergency
        self.needs_connected = needs_connected
        self.done = threading.Event()
        self.result = None
        self.exc = None
        self.abandoned = False


class Coordinator:
    """The only authority over the BLE transport (spec section 9).

    * every transport call runs on one worker thread (single writer);
    * ``emergency`` requests (watchdog, stop procedures) run before ``normal`` ones;
    * the last valid motor order wins; there are no leases;
    * stop profile is ``nobarrier``: no guarantee that ordinary orders cannot
      slip in between the stop requests of ``stop_all()``.

    Transport callbacks only update state under a lock and wake waiters; they never
    run user code.
    """

    STOP_PROFILE = "nobarrier"

    def __init__(self, transport, timing=None):
        self._t = transport
        self.timing = timing if timing is not None else Timing()
        self._lock = threading.RLock()
        self._cv = threading.Condition(self._lock)
        self._state = HubState.DISCONNECTED
        self._error = None
        self._link_lost = False
        self._loss_handled = False
        self._ports = {}      # conn -> PortEvent (attached devices only)
        self._modes = {}      # conn -> (type, mode) currently configured
        self._samples = {}    # conn -> last value bytes
        self._led_mode = -1
        self._button = False
        self._speeds = {}     # conn -> last commanded speed
        self._last_ok = 0.0
        self._last_port_change = 0.0
        self._qcv = threading.Condition(threading.Lock())
        self._emergency_q = collections.deque()
        self._normal_q = collections.deque()
        self._worker = None
        self._worker_stop = False
        self._wd = None
        self._wd_stop = threading.Event()
        self._wd_wake = threading.Event()

    # -- state ------------------------------------------------------------

    @property
    def state(self):
        return self._state

    def _set_state(self, new, error=None):
        with self._cv:
            old = self._state
            if new is old:
                return
            if new not in _TRANSITIONS[old]:
                raise InvalidStateError("invalid hub state transition %s -> %s" % (old.value, new.value))
            self._state = new
            self._error = error if new is HubState.ERROR else None
            self._cv.notify_all()

    def _force_error(self, cause):
        with self._cv:
            if self._state in (HubState.CONNECTED, HubState.CONNECTING):
                self._state = HubState.ERROR
                self._error = cause
                self._cv.notify_all()

    def _unusable(self):
        """Exception describing why the hub cannot take operations now, or None."""
        st = self._state
        if st is HubState.CONNECTED:
            return None
        if st in (HubState.CONNECTING, HubState.DISCONNECTING):
            return HubBusyError("hub is %s" % st.value)
        if st is HubState.ERROR:
            return HubDisconnectedError("hub connection lost: %s" % (self._error,))
        if st is HubState.SHUTDOWN:
            return InvalidStateError("hub was shut down; power it on and call connect()")
        return InvalidStateError("hub is not connected; call connect() first")

    def check_usable(self):
        exc = self._unusable()
        if exc is not None:
            raise exc

    # -- worker -----------------------------------------------------------

    def _start_worker(self):
        with self._qcv:
            self._worker_stop = False
            self._emergency_q.clear()
            self._normal_q.clear()
        self._worker = threading.Thread(target=self._worker_loop, name="wedopy-ble", daemon=True)
        self._worker.start()

    def _stop_worker(self):
        with self._qcv:
            self._worker_stop = True
            pending = list(self._emergency_q) + list(self._normal_q)
            self._emergency_q.clear()
            self._normal_q.clear()
            self._qcv.notify_all()
        for req in pending:
            req.exc = HubDisconnectedError("hub closed")
            req.done.set()
        w = self._worker
        if w is not None and w is not threading.current_thread():
            w.join(timeout=self.timing.op_timeout * 2 + 1.0)
        self._worker = None

    def _worker_loop(self):
        while True:
            with self._qcv:
                while not self._emergency_q and not self._normal_q and not self._worker_stop:
                    self._qcv.wait()
                if self._worker_stop:
                    return
                req = self._emergency_q.popleft() if self._emergency_q else self._normal_q.popleft()
            if req.abandoned:
                req.done.set()
                continue
            try:
                if req.needs_connected:
                    self.check_usable()
                req.result = req.fn()
                self._last_ok = time.monotonic()
            except Exception as exc:
                req.exc = exc
            req.done.set()

    def _enqueue(self, fn, emergency=False, needs_connected=True):
        req = _Request(fn, emergency, needs_connected)
        with self._qcv:
            if self._worker is None or self._worker_stop:
                raise InvalidStateError("hub is not connected; call connect() first")
            (self._emergency_q if emergency else self._normal_q).append(req)
            self._qcv.notify()
        return req

    def _submit(self, fn, emergency, needs_connected, timeout):
        req = self._enqueue(fn, emergency, needs_connected)
        # worst case: one in-flight operation (<= op_timeout) plus this one (<= timeout)
        if not req.done.wait(timeout + self.timing.op_timeout + 0.5):
            req.abandoned = True
            raise OperationTimeout("hub operation did not complete")
        if req.exc is not None:
            raise req.exc
        return req.result

    def _io(self, op, args, timeout):
        try:
            return getattr(self._t, op)(*args, timeout)
        except HubDisconnectedError as exc:
            self._on_link_lost(str(exc))
            raise
        except WedoError:
            raise
        except TimeoutError as exc:
            raise OperationTimeout(str(exc) or "BLE operation timed out") from exc
        except Exception as exc:
            raise BLEError(str(exc)) from exc

    def _call(self, op, *args, timeout=None, emergency=False, needs_connected=True):
        t = self.timing.op_timeout if timeout is None else timeout
        return self._submit(lambda: self._io(op, args, t), emergency, needs_connected, t)

    # -- notifications (transport thread) ----------------------------------

    def _on_notify(self, uuid, data):
        try:
            if uuid == K.CHAR_PORT:
                self._handle_port(data)
            elif uuid == K.CHAR_SENSOR:
                s = parse_sample(data)
                with self._cv:
                    self._samples[s.conn] = s.value
                    self._cv.notify_all()
            elif uuid == K.CHAR_BUTTON:
                if len(data) > 0:
                    self._button = data[0] != 0
            elif uuid == K.CHAR_DISCONNECT:
                self._on_link_lost("hub sent a Disconnect notification")
        except Exception:
            _log.debug("bad notification on %s: %s", uuid, hex_string(data), exc_info=True)

    def _handle_port(self, data):
        ev = parse_port_event(data)
        with self._cv:
            old = self._ports.get(ev.conn)
            if ev.attached:
                if old is not None and old.type == ev.type and old.hub_index == ev.hub_index:
                    return  # identical repeat: not activity, keeps the configured mode (spec 5.1)
                self._ports[ev.conn] = ev
            else:
                if old is None:
                    return
                del self._ports[ev.conn]
            self._modes.pop(ev.conn, None)   # a new/removed device starts at its default mode
            self._samples.pop(ev.conn, None)
            if ev.conn == K.CONN_RGB:
                self._led_mode = -1
            self._last_port_change = time.monotonic()
            self._cv.notify_all()

    def _on_link_lost(self, reason):
        with self._cv:
            if self._state in (HubState.DISCONNECTING, HubState.DISCONNECTED, HubState.SHUTDOWN):
                return
            self._link_lost = True
            self._force_error(reason)
            self._cv.notify_all()
            handle = not self._loss_handled
            self._loss_handled = True
        if handle and self._motors_active():
            # best-effort stop; runs off the transport thread
            threading.Thread(target=self._trip, args=("link lost: %s" % reason,),
                             name="wedopy-loss", daemon=True).start()

    # -- connection -------------------------------------------------------

    def connect(self):
        with self._cv:
            st = self._state
            if st is HubState.CONNECTED:
                return
            if st in (HubState.CONNECTING, HubState.DISCONNECTING):
                raise HubBusyError("hub is %s" % st.value)
            self._set_state(HubState.CONNECTING)
            self._ports.clear()
            self._modes.clear()
            self._samples.clear()
            self._speeds.clear()
            self._led_mode = -1
            self._button = False
            self._link_lost = False
            self._loss_handled = False
        tm = self.timing
        try:
            self._start_worker()
            self._t.set_callbacks(self._on_notify, self._on_link_lost)
            self._call("connect", timeout=tm.connect_timeout, needs_connected=False)
            for char in K.REQUIRED_CHARS:
                if not self._t.has_characteristic(char):
                    raise HubConnectionError("device does not look like a WeDo 2.0 hub: missing %s" % char)
            # The Disconnect notification is optional: some hubs do not support it (spec 8).
            self._optional("subscribe", K.CHAR_DISCONNECT)
            self._call("subscribe", K.CHAR_SENSOR, needs_connected=False)
            if self._t.has_characteristic(K.CHAR_BUTTON):
                self._optional("subscribe", K.CHAR_BUTTON)
                try:
                    data = self._call("read", K.CHAR_BUTTON, needs_connected=False)
                    self._button = len(data) > 0 and data[0] != 0
                except WedoError:
                    pass
            self._call("subscribe", K.CHAR_PORT, needs_connected=False)
            self._settle_ports(HubState.CONNECTING)
            with self._cv:
                if self._state is not HubState.CONNECTING:
                    raise self._unusable() or HubDisconnectedError("connection lost during connect")
                self._last_ok = time.monotonic()
                self._set_state(HubState.CONNECTED)
            self._start_watchdog()
        except BaseException as exc:
            self._abort_connect(exc)
            if isinstance(exc, WedoError) or not isinstance(exc, Exception):
                raise
            raise HubConnectionError(str(exc)) from exc

    def _optional(self, op, *args):
        try:
            self._call(op, *args, needs_connected=False)
        except WedoError as exc:
            _log.debug("optional %s %s unavailable: %s", op, args, exc)

    def _abort_connect(self, exc):
        with self._cv:
            if self._state is HubState.CONNECTING:
                self._state = HubState.ERROR
                self._error = str(exc)
                self._cv.notify_all()
        self._stop_watchdog()
        self._stop_worker()
        try:
            self._t.disconnect()
        except Exception:
            pass

    def _settle_ports(self, expected):
        """Wait until port events stop arriving (spec 5.1): 1.5 s quiet, 5 s at most."""
        tm = self.timing
        start = time.monotonic()
        with self._cv:
            self._last_port_change = max(self._last_port_change, start)
            while True:
                if self._state is not expected:
                    raise self._unusable() or HubDisconnectedError("connection lost during port discovery")
                now = time.monotonic()
                quiet_left = tm.settle_quiet - (now - self._last_port_change)
                max_left = tm.settle_max - (now - start)
                if quiet_left <= 0 or max_left <= 0:
                    return
                self._cv.wait(min(quiet_left, max_left))

    def disconnect(self):
        """Stop motors (best effort), close BLE, release resources.

        Returns True when no motor needed stopping or every stop was ACKed.
        """
        with self._cv:
            st = self._state
            if st in (HubState.DISCONNECTED, HubState.SHUTDOWN):
                if st is HubState.SHUTDOWN:
                    self._set_state(HubState.DISCONNECTED)
                return True
            if st in (HubState.CONNECTING, HubState.DISCONNECTING):
                raise HubBusyError("hub is %s" % st.value)
            link_lost = self._link_lost
            self._set_state(HubState.DISCONNECTING)
        confirmed = True
        if not link_lost:
            confirmed, _ = self._stop_motors(self.timing.emergency_attempts,
                                             self.timing.emergency_attempt_timeout)
        elif self._motors_active():
            confirmed = False
        self._stop_watchdog()
        self._stop_worker()
        try:
            self._t.disconnect()
        except Exception:
            _log.debug("transport disconnect failed", exc_info=True)
        with self._cv:
            if confirmed:
                self._speeds.clear()
            self._state = HubState.DISCONNECTED
            self._error = None
            self._cv.notify_all()
        if not confirmed:
            _log.warning("disconnect: motor stop could not be confirmed")
        return confirmed

    def shutdown_hub(self):
        """Ask the hub to power off. Declared shut down only after an ACK (spec 8)."""
        self.check_usable()
        self._call("write", K.CHAR_TURN_OFF, b"\x01")
        with self._cv:
            self._set_state(HubState.SHUTDOWN)
        self._stop_watchdog()
        self._stop_worker()
        try:
            self._t.disconnect()
        except Exception:
            pass

    # -- ports ------------------------------------------------------------

    def ports_raw(self):
        """Copy of the known devices: ``{connect_id: device_type}`` (internal ones included)."""
        with self._lock:
            return {c: ev.type for c, ev in self._ports.items()}

    def refresh_ports(self):
        self.check_usable()
        with self._cv:
            self._ports.clear()
            self._modes.clear()
            self._samples.clear()
            self._led_mode = -1
            self._last_port_change = time.monotonic()
        self._call("unsubscribe", K.CHAR_PORT)
        self._call("subscribe", K.CHAR_PORT)
        self._settle_ports(HubState.CONNECTED)

    def _require_device(self, conn, typ):
        with self._lock:
            ev = self._ports.get(conn)
        if ev is None:
            raise DeviceNotFoundError("no device on connect id %d" % conn)
        if ev.type != typ:
            raise DeviceTypeError("device on connect id %d is a %s, expected a %s" % (
                conn, K.TYPE_NAMES.get(ev.type, "0x%02x" % ev.type), K.TYPE_NAMES.get(typ, "0x%02x" % typ)))

    # -- outputs ----------------------------------------------------------

    def _motors_active(self):
        with self._lock:
            return any(s != 0 for s in self._speeds.values())

    def set_motor(self, conn, speed):
        self.check_usable()
        self._require_device(conn, K.TYPE_MOTOR)
        data = motor_power(conn, speed)
        with self._lock:
            was_active = any(s != 0 for s in self._speeds.values())
            if speed != 0:
                self._speeds[conn] = speed
                if not was_active:
                    self._last_ok = time.monotonic()
        if speed != 0:
            self._wd_wake.set()
        self._call("write", K.CHAR_OUTPUT_CMD, data)
        if speed == 0:
            with self._lock:
                self._speeds[conn] = 0

    def stop_all(self):
        """Stop every known motor. Raises the first error after trying all of them."""
        self.check_usable()
        with self._lock:
            conns = sorted(set(c for c, ev in self._ports.items() if ev.type == K.TYPE_MOTOR)
                           | set(self._speeds))
        first = None
        for conn in conns:
            try:
                self._call("write", K.CHAR_OUTPUT_CMD, motor_power(conn, 0), emergency=True)
            except Exception as exc:
                if first is None:
                    first = exc
            else:
                with self._lock:
                    self._speeds[conn] = 0
        if first is not None:
            raise first

    def _ensure_led_mode(self, mode):
        with self._lock:
            if self._led_mode == mode:
                return
        self._call("write", K.CHAR_INPUT_CMD,
                   input_format(K.CONN_RGB, K.TYPE_RGB, mode, 1, K.UNIT_RAW, True))
        with self._lock:
            self._led_mode = mode

    def led_index(self, index):
        self.check_usable()
        self._ensure_led_mode(K.LED_DISCRETE)
        self._call("write", K.CHAR_OUTPUT_CMD, led_index(index))

    def led_rgb(self, r, g, b):
        self.check_usable()
        self._ensure_led_mode(K.LED_ABSOLUTE)
        self._call("write", K.CHAR_OUTPUT_CMD, led_rgb(r, g, b))

    # -- inputs -----------------------------------------------------------

    def button_pressed(self):
        self.check_usable()
        return self._button

    def read_sensor(self, conn, typ, mode, unit, expected_len=None, timeout=None):
        """Configure the sensor once, then return the last value received.

        The hub notifies only when the value changes, so an unchanged value stays valid
        while the link is up (spec 5.3).
        """
        self.check_usable()
        self._require_device(conn, typ)
        wait = self.timing.sensor_timeout if timeout is None else timeout
        key = (typ, mode)
        with self._cv:
            need = self._modes.get(conn) != key
            if need:
                self._samples.pop(conn, None)
                self._modes[conn] = key
        if need:
            try:
                self._call("write", K.CHAR_INPUT_CMD, input_format(conn, typ, mode, 1, unit, True))
                self._call("write", K.CHAR_INPUT_CMD, input_start(conn))
            except BaseException:
                with self._cv:
                    if self._modes.get(conn) == key:
                        del self._modes[conn]
                raise
        deadline = time.monotonic() + wait
        with self._cv:
            while True:
                exc = self._unusable()
                if exc is not None:
                    raise exc
                if conn not in self._ports:
                    raise DeviceNotFoundError("the device on connect id %d was disconnected" % conn)
                if self._modes.get(conn) != key:
                    raise DeviceNotFoundError("the device on connect id %d changed" % conn)
                value = self._samples.get(conn)
                if value is not None and (expected_len is None or len(value) == expected_len):
                    return value
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise OperationTimeout("the hub sent no value within %.1f s" % wait)
                self._cv.wait(remaining)

    # -- watchdog ---------------------------------------------------------

    def _start_watchdog(self):
        self._wd_stop.clear()
        self._wd_wake.clear()
        self._wd = threading.Thread(target=self._watchdog_loop, name="wedopy-watchdog", daemon=True)
        self._wd.start()

    def _stop_watchdog(self):
        self._wd_stop.set()
        self._wd_wake.set()
        w = self._wd
        if w is not None and w is not threading.current_thread():
            w.join(timeout=2.0)
        self._wd = None

    def _watchdog_loop(self):
        """Heartbeat + timeout supervision, independent of the user's task scheduler.

        The heartbeat is a Battery Level read with response (spec 10.1). It is queued with
        emergency priority so a long queue of ordinary orders cannot starve it.
        """
        tm = self.timing
        hb = None
        next_hb = 0.0
        while not self._wd_stop.is_set():
            if self._state is not HubState.CONNECTED or not self._motors_active():
                hb = None
                self._wd_wake.wait(0.1)
                self._wd_wake.clear()
                continue
            now = time.monotonic()
            if hb is not None and hb.done.is_set():
                hb = None
            if hb is None and now >= next_hb:
                next_hb = now + tm.heartbeat_interval
                try:
                    hb = self._enqueue(
                        lambda: self._io("read", (K.CHAR_BATTERY,), tm.op_timeout),
                        emergency=True, needs_connected=False)
                except WedoError:
                    hb = None
            if now - self._last_ok > tm.watchdog_timeout:
                self._trip("no valid ACK from the hub for %.1f s" % (now - self._last_ok))
                hb = None
                continue
            self._wd_stop.wait(tm.poll)

    def _stop_motors(self, attempts, attempt_timeout):
        """Write speed 0 to every known motor with emergency priority.

        Returns ``(confirmed, per_attempt_ok)``.
        """
        with self._lock:
            pending = sorted(set(c for c, ev in self._ports.items() if ev.type == K.TYPE_MOTOR)
                             | set(self._speeds))
        results = []
        for _ in range(attempts):
            if not pending:
                break
            still = []
            for conn in pending:
                try:
                    self._call("write", K.CHAR_OUTPUT_CMD, motor_power(conn, 0),
                               timeout=attempt_timeout, emergency=True, needs_connected=False)
                except Exception:
                    still.append(conn)
                else:
                    with self._lock:
                        self._speeds[conn] = 0
            pending = still
            results.append(not pending)
        return (not pending), results

    def _trip(self, reason):
        """Emergency stop (spec 10.3): prioritised stop attempts, log, then state ``error``."""
        _wlog.error("watchdog: %s", reason)
        tm = self.timing
        confirmed, results = self._stop_motors(tm.emergency_attempts, tm.emergency_attempt_timeout)
        parts = []
        for i, ok in enumerate(results, 1):
            parts.append(("stop attempt %d" if i == 1 else "attempt %d") % i + (" ACK" if ok else " no ACK"))
            if ok:
                break
        if confirmed:
            _wlog.warning("watchdog: %s", ", ".join(parts))
            _wlog.warning("watchdog: motors stopped")
        else:
            _wlog.error("watchdog: stop NOT confirmed (%d attempts)", tm.emergency_attempts)
        self._force_error(reason)
