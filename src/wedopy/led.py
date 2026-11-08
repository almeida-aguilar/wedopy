"""Built-in LED (spec 5.5)."""

# Colour index constants (discrete mode 0..10)
OFF = 0
BLACK = 0
PINK = 1
PURPLE = 2
VIOLET = 2
BLUE = 3
CYAN = 4
SKY_BLUE = 4
LIGHT_BLUE = 4
GREEN = 5
YELLOW = 6
ORANGE = 7
RED = 8
WHITE = 9
BRIGHT_WHITE = 9
DIM_WHITE = 10
SOFT_WHITE = 10

# Spanish aliases
APAGADO = OFF
ROSA = PINK
MORADO = PURPLE
AZUL = BLUE
CIAN = CYAN
CELESTE = SKY_BLUE
VERDE = GREEN
AMARILLO = YELLOW
NARANJA = ORANGE
ROJO = RED
BLANCO = WHITE
BLANCO_TENUE = DIM_WHITE

__all__ = [
    "LED",
    "OFF",
    "BLACK",
    "PINK",
    "PURPLE",
    "VIOLET",
    "BLUE",
    "CYAN",
    "SKY_BLUE",
    "LIGHT_BLUE",
    "GREEN",
    "YELLOW",
    "ORANGE",
    "RED",
    "WHITE",
    "BRIGHT_WHITE",
    "DIM_WHITE",
    "SOFT_WHITE",
    "APAGADO",
    "ROSA",
    "MORADO",
    "AZUL",
    "CIAN",
    "CELESTE",
    "VERDE",
    "AMARILLO",
    "NARANJA",
    "ROJO",
    "BLANCO",
    "BLANCO_TENUE",
]


def _byte(name, value, hi):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("%s must be an int, not %s" % (name, type(value).__name__))
    if not 0 <= value <= hi:
        raise ValueError("%s must be in 0..%d, got %d" % (name, hi, value))
    return value


class LED:
    """Indexed colours (0..10) and RGB are different hub modes; the core tracks which is active."""

    OFF = OFF
    BLACK = BLACK
    PINK = PINK
    PURPLE = PURPLE
    VIOLET = VIOLET
    BLUE = BLUE
    CYAN = CYAN
    SKY_BLUE = SKY_BLUE
    LIGHT_BLUE = LIGHT_BLUE
    GREEN = GREEN
    YELLOW = YELLOW
    ORANGE = ORANGE
    RED = RED
    WHITE = WHITE
    BRIGHT_WHITE = BRIGHT_WHITE
    DIM_WHITE = DIM_WHITE
    SOFT_WHITE = SOFT_WHITE

    # Spanish aliases
    APAGADO = APAGADO
    ROSA = ROSA
    MORADO = MORADO
    AZUL = AZUL
    CIAN = CIAN
    CELESTE = CELESTE
    VERDE = VERDE
    AMARILLO = AMARILLO
    NARANJA = NARANJA
    ROJO = ROJO
    BLANCO = BLANCO
    BLANCO_TENUE = BLANCO_TENUE

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
