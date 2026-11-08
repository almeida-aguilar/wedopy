"""Built-in LED (spec 5.5)."""


def _byte(name, value, hi):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("%s must be an int, not %s" % (name, type(value).__name__))
    if not 0 <= value <= hi:
        raise ValueError("%s must be in 0..%d, got %d" % (name, hi, value))
    return value


class LED:
    """Indexed colours (0..10) and RGB are different hub modes; the core tracks which is active."""

    def __init__(self, session):
        self._session = session

    def on(self):
        """White."""
        self.rgb(255, 255, 255)

    def off(self):
        self.rgb(0, 0, 0)

    def index(self, index):
        self._session.core.led_index(_byte("index", index, 10))

    def rgb(self, red, green, blue):
        self._session.core.led_rgb(_byte("red", red, 255), _byte("green", green, 255),
                                   _byte("blue", blue, 255))
