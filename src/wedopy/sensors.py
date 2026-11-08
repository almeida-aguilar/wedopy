"""Distance and tilt sensors (spec 5.3 and 5.4)."""
import math

from wedopy_core import _wedopy as _core
from wedopy_core.exceptions import BLEError
from wedopy_core.protocol import constants as K


def _decode(fn, raw):
    try:
        return fn(raw)
    except ValueError as exc:
        raise BLEError("unexpected sensor value %s: %s" % (_core.hex_string(raw), exc)) from exc


class DistanceSensor:
    """Distance sensor. Values are normalised integers 0..10, not centimetres."""

    def __init__(self, session, conn, port):
        self._session = session
        self._conn = conn
        self.port = port

    def read(self):
        raw = self._session.core.read_sensor(self._conn, K.TYPE_MOTION, K.DISTANCE_DETECT, K.UNIT_SI)
        value = _decode(_core.decode_scalar, raw)
        if not math.isfinite(value):
            raise BLEError("the distance sensor reported a non-finite value")
        return max(0, min(10, int(round(value))))

    @staticmethod
    def _threshold(threshold):
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
            raise TypeError("threshold must be a number")
        if not math.isfinite(threshold) or not 0 <= threshold <= 10:
            raise ValueError("threshold must be a finite number in 0..10")
        return threshold

    def is_near(self, threshold):
        """True when ``read() < threshold`` (strict)."""
        t = self._threshold(threshold)
        return self.read() < t

    def is_far(self, threshold):
        """True when ``read() > threshold`` (strict)."""
        t = self._threshold(threshold)
        return self.read() > t

    def __repr__(self):
        return "DistanceSensor(%r)" % self.port


class TiltSensor:
    """Tilt sensor. With the logo up and the connector towards you: +x is right, +y is forward.

    The WeDo 2.0 tilt sensor is a 4-position switch, not an accelerometer.
    Two of its three documented modes are actually usable on real hardware:

    * Direction mode (1) uses ``UNIT_SI`` and a 4-byte ``float32`` payload.
      Values 0, 3, 5, 7, 9 map to neutral/back/right/left/forward.
    * Angle mode (0) **requires** ``UNIT_RAW`` and a 2-byte ``int8`` pair.
      With ``UNIT_SI`` the hub accepts the command but never notifies.
    * Bump mode (2) is accepted by the hub but never emits; the firmware
      does not implement it.

    (All three verified on hardware, Nov 2026.)

    Like every sensor on the hub, reads only return a fresh value when the
    physical quantity changes. A stationary sensor produces no new samples,
    so move or incline it after configuring a read.
    """

    def __init__(self, session, conn, port):
        self._session = session
        self._conn = conn
        self.port = port

    def read_angle(self):
        """``(x, y)`` in degrees, nominally -45..45 (a shake can exceed that).

        Uses ``UNIT_RAW`` and expects the 2-byte ``int8`` pair the hub
        actually sends; the SI-unit 8-byte form documented in the protocol
        spec does not exist in this firmware.
        """
        raw = self._session.core.read_sensor(self._conn, K.TYPE_TILT, K.TILT_ANGLE, K.UNIT_RAW,
                                             expected_len=2)
        return _decode(_core.decode_tilt_angle, raw)

    def read_direction(self):
        """One of ``neutral``, ``back``, ``right``, ``left``, ``forward``."""
        raw = self._session.core.read_sensor(self._conn, K.TYPE_TILT, K.TILT_DIRECTION, K.UNIT_SI,
                                             expected_len=4)
        return _decode(_core.tilt_direction_name, raw)

    def __repr__(self):
        return "TiltSensor(%r)" % self.port
