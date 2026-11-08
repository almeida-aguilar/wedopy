"""Motors (spec 5.2)."""


def _check_speed(speed):
    if isinstance(speed, bool) or not isinstance(speed, int):
        raise TypeError("speed must be an int in -100..100, not %s" % type(speed).__name__)
    if not -100 <= speed <= 100:
        raise ValueError("speed must be in -100..100, got %d" % speed)
    return speed


class Motor:
    """A motor on port ``A`` or ``B``. The sign of ``speed`` is a logical direction."""

    def __init__(self, session, conn, port):
        self._session = session
        self._conn = conn
        self.port = port

    def run(self, speed):
        """Set the logical speed, -100..100. ``run(0)`` is ``stop()``."""
        self._session.core.set_motor(self._conn, _check_speed(speed))

    def stop(self):
        """Ask the motor to stop. An ACK confirms communication, not that the shaft stopped."""
        self._session.core.set_motor(self._conn, 0)

    def __repr__(self):
        return "Motor(%r)" % self.port


class MotorGroup:
    """Several motors driven in deterministic order (A, then B). Not atomic."""

    def __init__(self, motors):
        self._motors = sorted(motors, key=lambda m: m.port)

    def run(self, speed):
        speed = _check_speed(speed)
        for m in self._motors:
            m.run(speed)

    def stop(self):
        first = None
        for m in self._motors:
            try:
                m.stop()
            except Exception as exc:
                if first is None:
                    first = exc
        if first is not None:
            raise first

    def __repr__(self):
        return "MotorGroup(%s)" % ", ".join(repr(m.port) for m in self._motors)
