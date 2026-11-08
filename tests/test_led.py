import pytest
from helpers import make_hub

from wedopy import (
    LED,
    OFF, BLACK, PINK, PURPLE, VIOLET, BLUE, CYAN, SKY_BLUE, LIGHT_BLUE,
    GREEN, YELLOW, ORANGE, RED, WHITE, BRIGHT_WHITE, DIM_WHITE, SOFT_WHITE,
    APAGADO, ROSA, MORADO, AZUL, CIAN, CELESTE, VERDE, AMARILLO, NARANJA, ROJO,
    BLANCO, BLANCO_TENUE,
)
from wedopy_core.protocol import constants as K


def test_index_sets_discrete_mode_once():
    hub, sim = make_hub()
    with hub:
        hub.led.index(6)
        hub.led.index(9)
        assert sim.writes_to(K.CHAR_INPUT_CMD) == [bytes.fromhex("0102061701010000000001")]
        assert sim.writes_to(K.CHAR_OUTPUT_CMD) == [bytes.fromhex("06040106"), bytes.fromhex("06040109")]


def test_rgb_and_index_do_not_get_confused():
    hub, sim = make_hub()
    with hub:
        hub.led.index(4)
        hub.led.rgb(0, 255, 64)
        hub.led.index(4)
        modes = [w[4] for w in sim.writes_to(K.CHAR_INPUT_CMD)]
        assert modes == [K.LED_DISCRETE, K.LED_ABSOLUTE, K.LED_DISCRETE]
        assert sim.writes_to(K.CHAR_OUTPUT_CMD)[1] == bytes.fromhex("06040300ff40")


def test_on_is_white_and_off_is_black():
    hub, sim = make_hub()
    with hub:
        hub.led.on()
        hub.led.off()
        out = sim.writes_to(K.CHAR_OUTPUT_CMD)
        assert out == [bytes.fromhex("060403ffffff"), bytes.fromhex("060403000000")]


@pytest.mark.parametrize("bad", [-1, 11])
def test_index_range(bad):
    hub, sim = make_hub()
    with hub:
        with pytest.raises(ValueError):
            hub.led.index(bad)


@pytest.mark.parametrize("bad", [1.0, True, "1"])
def test_index_type(bad):
    hub, sim = make_hub()
    with hub:
        with pytest.raises(TypeError):
            hub.led.index(bad)


def test_rgb_validation():
    hub, sim = make_hub()
    with hub:
        with pytest.raises(ValueError):
            hub.led.rgb(256, 0, 0)
        with pytest.raises(TypeError):
            hub.led.rgb(0, 0.5, 0)
        assert not sim.writes_to(K.CHAR_OUTPUT_CMD)


def test_color_constants_values():
    assert OFF == 0
    assert BLACK == 0
    assert PINK == 1
    assert PURPLE == 2
    assert VIOLET == 2
    assert BLUE == 3
    assert CYAN == 4
    assert SKY_BLUE == 4
    assert LIGHT_BLUE == 4
    assert GREEN == 5
    assert YELLOW == 6
    assert ORANGE == 7
    assert RED == 8
    assert WHITE == 9
    assert BRIGHT_WHITE == 9
    assert DIM_WHITE == 10
    assert SOFT_WHITE == 10


def test_spanish_aliases_values():
    assert APAGADO == OFF
    assert ROSA == PINK
    assert MORADO == PURPLE
    assert AZUL == BLUE
    assert CIAN == CYAN
    assert CELESTE == SKY_BLUE
    assert VERDE == GREEN
    assert AMARILLO == YELLOW
    assert NARANJA == ORANGE
    assert ROJO == RED
    assert BLANCO == WHITE
    assert BLANCO_TENUE == DIM_WHITE


def test_class_and_instance_attributes():
    hub, _ = make_hub()
    for name in ["OFF", "BLACK", "PINK", "PURPLE", "VIOLET", "BLUE", "CYAN",
                 "SKY_BLUE", "LIGHT_BLUE", "GREEN", "YELLOW", "ORANGE", "RED",
                 "WHITE", "BRIGHT_WHITE", "DIM_WHITE", "SOFT_WHITE", "APAGADO",
                 "ROSA", "MORADO", "AZUL", "CIAN", "CELESTE", "VERDE",
                 "AMARILLO", "NARANJA", "ROJO", "BLANCO", "BLANCO_TENUE"]:
        val = globals()[name]
        assert getattr(LED, name) == val
        assert getattr(hub.led, name) == val


def test_index_with_constants():
    hub, sim = make_hub()
    with hub:
        hub.led.index(GREEN)
        hub.led.index(LED.RED)
        hub.led.index(hub.led.BLUE)
        hub.led.index(AMARILLO)
        assert sim.writes_to(K.CHAR_OUTPUT_CMD) == [
            bytes.fromhex("06040105"),
            bytes.fromhex("06040108"),
            bytes.fromhex("06040103"),
            bytes.fromhex("06040106"),
        ]
