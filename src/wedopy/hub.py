"""``Hub``: the physical WeDo 2.0 Smart Hub (spec 5.1)."""
from wedopy_core.exceptions import (
    AmbiguousDeviceError,
    DeviceNotFoundError,
    DeviceTypeError,
)
from wedopy_core.protocol import constants as K

from .button import Button
from .led import LED
from .motor import Motor, MotorGroup
from .sensors import DistanceSensor, TiltSensor
from .session import Session

_PORTS = {"A": K.CONN_PORT_A, "B": K.CONN_PORT_B}
_CONN_PORT = {v: k for k, v in _PORTS.items()}


def _port_conn(port):
    if not isinstance(port, str):
        raise TypeError("port must be 'A' or 'B', not %s" % type(port).__name__)
    conn = _PORTS.get(port.upper())
    if conn is None:
        raise ValueError("port must be 'A' or 'B', got %r" % port)
    return conn


class Hub:
    """Create it, then ``connect()`` or use it as a context manager (recommended)::

        with Hub() as hub:
            hub.motor("A").run(100)

    ``transport`` and ``timing`` are for tests and tuning; leave them out in normal use.
    """

    def __init__(self, *, transport=None, timing=None):
        self._session = Session(transport, timing)
        self._led = LED(self._session)
        self._button = Button(self._session)

    # -- lifecycle ----------------------------------------------------------

    def connect(self):
        """Connect to the first WeDo 2.0 hub found. Returns ``self``."""
        self._session.connect()
        return self

    @property
    def is_connected(self):
        return self._session.is_connected

    def disconnect(self):
        """Cancel tasks, try to stop the motors, close BLE. Safe to call twice."""
        self._session.disconnect()

    def shutdown(self):
        """Ask the hub to power off. It must be switched on by hand afterwards."""
        self._session.shutdown()

    def stop_all(self):
        """Ask every motor to stop (``nobarrier`` profile: no ordering guarantee against other orders)."""
        self._session.stop_all()

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc, tb):
        try:
            self.disconnect()
        except Exception:
            if exc_type is None:
                raise
        return False

    # -- ports and devices ----------------------------------------------------

    @property
    def ports(self):
        """Snapshot of the known external devices, e.g. ``{"A": "motor", "B": "distance"}``."""
        raw = self._session.ports_raw()
        return {name: K.TYPE_NAMES.get(raw[conn], "unknown(0x%02x)" % raw[conn])
                for name, conn in _PORTS.items() if conn in raw}

    def refresh_ports(self):
        """Ask the hub to report its devices again and return the new snapshot."""
        self._session.refresh_ports()
        return self.ports

    def _select(self, type_code, port):
        self._session.core.check_usable()
        raw = self._session.ports_raw()
        wanted = K.TYPE_NAMES[type_code]
        if port is not None:
            conn = _port_conn(port)
            found = raw.get(conn)
            label = port.upper()
            if found is None:
                raise DeviceNotFoundError("nothing is connected to port %s" % label)
            if found != type_code:
                raise DeviceTypeError("port %s holds a %s, not a %s" % (
                    label, K.TYPE_NAMES.get(found, "unknown device"), wanted))
            return conn
        candidates = [c for c in (K.CONN_PORT_A, K.CONN_PORT_B) if raw.get(c) == type_code]
        if not candidates:
            raise DeviceNotFoundError("no %s is connected" % wanted)
        if len(candidates) > 1:
            raise AmbiguousDeviceError("more than one %s is connected; pass the port ('A' or 'B')" % wanted)
        return candidates[0]

    def motor(self, port=None):
        conn = self._select(K.TYPE_MOTOR, port)
        return Motor(self._session, conn, _CONN_PORT[conn])

    def motors(self, ports):
        """A group of motors, e.g. ``hub.motors(("A", "B"))``; driven A first, then B."""
        if isinstance(ports, str):
            raise TypeError("ports must be a sequence such as ('A', 'B')")
        ports = list(ports)
        if not ports:
            raise ValueError("ports must not be empty")
        conns = [_port_conn(p) for p in ports]
        if len(set(conns)) != len(conns):
            raise ValueError("duplicate port in %r" % (ports,))
        return MotorGroup([self.motor(_CONN_PORT[c]) for c in conns])

    def distance_sensor(self, port=None):
        conn = self._select(K.TYPE_MOTION, port)
        return DistanceSensor(self._session, conn, _CONN_PORT[conn])

    def tilt_sensor(self, port=None):
        conn = self._select(K.TYPE_TILT, port)
        return TiltSensor(self._session, conn, _CONN_PORT[conn])

    @property
    def led(self):
        return self._led

    @property
    def button(self):
        return self._button

    @property
    def tasks(self):
        """Cooperative task manager of this hub (``add`` / ``wait`` / ``cancel``)."""
        return self._session.tasks
