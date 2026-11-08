import pytest
from helpers import make_hub

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
