"""In-memory WeDo 2.0 hub for tests and demos (spec 15.3).

Reproduces what was observed on real hardware: a burst of internal devices on subscribing
to port notifications, external devices reported later, optional repeated port events,
sensor values notified once after the start signal and then only on change.

Fault injection: :meth:`freeze` (no ACKs), :meth:`drop_link`, ``ack_delay``,
``silent_sensors``, ``fail_connect``, ``fail_reads``.
"""
import struct
import threading
import time

from wedopy_core.exceptions import BLEError, HubConnectionError, HubDisconnectedError, OperationTimeout
from wedopy_core.protocol import constants as K
from .interfaces import Transport

_TYPE_BY_NAME = {"motor": K.TYPE_MOTOR, "distance": K.TYPE_MOTION, "tilt": K.TYPE_TILT}
_PORT_CONN = {"A": K.CONN_PORT_A, "B": K.CONN_PORT_B}
_INTERNAL = ((K.CONN_CURRENT, K.TYPE_CURRENT), (K.CONN_VOLTAGE, K.TYPE_VOLTAGE),
             (K.CONN_PIEZO, K.TYPE_PIEZO), (K.CONN_RGB, K.TYPE_RGB))
_DIRECTION_CODES = {"neutral": 0, "back": 3, "right": 5, "left": 7, "forward": 9}


def attach_event(conn, typ):
    return bytes((conn, 0x01, 0x00, typ, 0, 0, 0, 0x10, 0, 0, 0, 0x10))


class SimulatedHub(Transport):
    def __init__(self, devices=None, *, external_delay=0.05, repeat_ports=None,
                 ack_delay=0.0, silent_sensors=False, fail_connect=False):
        self.devices = dict(devices if devices is not None else {"A": "motor", "B": "distance"})
        self.external_delay = external_delay
        self.repeat_ports = repeat_ports      # seconds between duplicate port events, or None
        self.ack_delay = ack_delay
        self.silent_sensors = silent_sensors
        self.fail_connect = fail_connect
        self.fail_reads = False               # reads raise BLEError (heartbeat failure)
        self.frozen = False
        self.dropped = False
        self.connected = False
        self.supports_disconnect_notify = False
        self.writes = []                      # [(uuid, bytes)]
        self.reads = []                       # [uuid]
        self.motors = {}                      # conn -> signed speed last written
        self.sensor_modes = {}                # conn -> (type, mode)
        self.led_mode = None
        self.button = False
        self.distance = 0
        self.tilt_angle = (0.0, 0.0)
        self.tilt_code = 0
        self._notifying = set()
        self._on_notify = None
        self._on_disconnect = None
        self._lock = threading.RLock()
        self._closed = threading.Event()

    # -- test controls ----------------------------------------------------

    def freeze(self):
        """Stop ACKing: operations block until their timeout, then raise OperationTimeout."""
        self.frozen = True

    def unfreeze(self):
        self.frozen = False

    def drop_link(self, reason="simulated link loss"):
        self.dropped = True
        self.connected = False
        cb = self._on_disconnect
        if cb is not None:
            cb(reason)

    def writes_to(self, uuid):
        with self._lock:
            return [d for u, d in self.writes if u == uuid]

    def press(self):
        self.button = True
        self._notify(K.CHAR_BUTTON, b"\x01")

    def release(self):
        self.button = False
        self._notify(K.CHAR_BUTTON, b"\x00")

    def set_distance(self, value):
        self.distance = value
        self._push_values(K.TYPE_MOTION)

    def set_tilt_angle(self, x, y):
        self.tilt_angle = (float(x), float(y))
        self._push_values(K.TYPE_TILT, mode=K.TILT_ANGLE)

    def set_tilt_direction(self, name):
        self.tilt_code = _DIRECTION_CODES[name] if isinstance(name, str) else int(name)
        self._push_values(K.TYPE_TILT, mode=K.TILT_DIRECTION)

    def attach(self, port, kind):
        self.devices[port] = kind
        self._notify(K.CHAR_PORT, attach_event(_PORT_CONN[port], _TYPE_BY_NAME[kind]))

    def detach(self, port):
        self.devices.pop(port, None)
        self._notify(K.CHAR_PORT, bytes((_PORT_CONN[port], 0x00)))

    # -- Transport --------------------------------------------------------

    def set_callbacks(self, on_notify, on_disconnect):
        self._on_notify = on_notify
        self._on_disconnect = on_disconnect

    def connect(self, timeout):
        if self.fail_connect:
            raise HubConnectionError("no WeDo 2.0 hub found")
        self.dropped = False
        self.connected = True
        self._closed.clear()

    def disconnect(self, timeout=None):
        self.connected = False
        self._notifying.clear()
        self._closed.set()

    def has_characteristic(self, uuid):
        if uuid == K.CHAR_DISCONNECT:
            return True
        return uuid in (K.CHAR_BATTERY, K.CHAR_PORT, K.CHAR_SENSOR, K.CHAR_INPUT_CMD,
                        K.CHAR_OUTPUT_CMD, K.CHAR_BUTTON, K.CHAR_TURN_OFF)

    def _gate(self, timeout):
        if self.dropped or not self.connected:
            raise HubDisconnectedError("simulated link is down")
        if self.frozen:
            time.sleep(timeout)
            raise OperationTimeout("no ACK from the simulated hub")
        if self.ack_delay:
            time.sleep(self.ack_delay)
            if self.dropped:
                raise HubDisconnectedError("simulated link is down")

    def read(self, uuid, timeout):
        self._gate(timeout)
        if self.fail_reads:
            raise BLEError("simulated read failure")
        with self._lock:
            self.reads.append(uuid)
        if uuid == K.CHAR_BATTERY:
            return bytes((87,))
        if uuid == K.CHAR_BUTTON:
            return bytes((1 if self.button else 0,))
        raise BLEError("characteristic not readable: %s" % uuid)

    def write(self, uuid, data, timeout):
        self._gate(timeout)
        data = bytes(data)
        with self._lock:
            self.writes.append((uuid, data))
        if uuid == K.CHAR_OUTPUT_CMD:
            if len(data) == 4 and data[1] == 0x01 and data[2] == 0x01:
                self.motors[data[0]] = struct.unpack("b", data[3:4])[0]
        elif uuid == K.CHAR_INPUT_CMD:
            if len(data) >= 5 and data[0] == 0x01 and data[1] == 0x02:
                conn, typ, mode = data[2], data[3], data[4]
                self.sensor_modes[conn] = (typ, mode)
                if conn == K.CONN_RGB:
                    self.led_mode = mode
            elif len(data) == 3 and data[0] == 0x00 and data[1] == 0x01:
                self._push_conn(data[2])

    def subscribe(self, uuid, timeout):
        self._gate(timeout)
        if uuid == K.CHAR_DISCONNECT and not self.supports_disconnect_notify:
            raise BLEError("notifications not supported on this characteristic")
        self._notifying.add(uuid)
        if uuid == K.CHAR_PORT:
            threading.Thread(target=self._port_burst, name="sim-ports", daemon=True).start()

    def unsubscribe(self, uuid, timeout):
        self._gate(timeout)
        self._notifying.discard(uuid)

    # -- internals --------------------------------------------------------

    def _notify(self, uuid, data):
        cb = self._on_notify
        if cb is not None and uuid in self._notifying:
            cb(uuid, bytes(data))

    def _port_burst(self):
        for conn, typ in _INTERNAL:
            self._notify(K.CHAR_PORT, attach_event(conn, typ))
        if self._closed.wait(self.external_delay):
            return
        events = [attach_event(_PORT_CONN[p], _TYPE_BY_NAME[k]) for p, k in sorted(self.devices.items())]
        for ev in events:
            self._notify(K.CHAR_PORT, ev)
        while self.repeat_ports and K.CHAR_PORT in self._notifying:
            if self._closed.wait(self.repeat_ports):
                return
            for ev in events:
                self._notify(K.CHAR_PORT, ev)

    def _value_bytes(self, conn):
        typ, mode = self.sensor_modes.get(conn, (None, None))
        if typ == K.TYPE_MOTION:
            return struct.pack("<f", float(self.distance))
        if typ == K.TYPE_TILT:
            if mode == K.TILT_ANGLE:
                return struct.pack("<ff", *self.tilt_angle)
            return struct.pack("<f", float(self.tilt_code))
        return None

    def _push_conn(self, conn):
        if self.silent_sensors:
            return
        value = self._value_bytes(conn)
        if value is not None:
            self._notify(K.CHAR_SENSOR, bytes((0x01, conn)) + value)

    def _push_values(self, typ, mode=None):
        for conn, (t, m) in list(self.sensor_modes.items()):
            if t == typ and (mode is None or m == mode):
                self._push_conn(conn)
