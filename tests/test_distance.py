import pytest
from helpers import make_hub

from wedopy import DeviceNotFoundError, HubDisconnectedError, OperationTimeout
from wedopy_core.protocol import constants as K


def test_first_read_configures_once_then_returns_last_value():
    hub, sim = make_hub({"A": "motor", "B": "distance"})
    with hub:
        s = hub.distance_sensor("B")
        sim.set_distance(7)
        assert s.read() == 7
        assert sim.writes_to(K.CHAR_INPUT_CMD) == [
            bytes.fromhex("0102022300010000000201"),     # SI unit, detect mode, notify on change
            bytes.fromhex("000102"),                     # start signal
        ]
        assert s.read() == 7                             # unchanged value stays valid
        assert len(sim.writes_to(K.CHAR_INPUT_CMD)) == 2
        sim.set_distance(2)
        assert s.read() == 2
        assert len(sim.writes_to(K.CHAR_INPUT_CMD)) == 2


def test_read_returns_int_in_range():
    hub, sim = make_hub()
    with hub:
        s = hub.distance_sensor("B")
        sim.distance = 10
        v = s.read()
        assert isinstance(v, int) and v == 10


def test_is_near_and_is_far_are_strict():
    hub, sim = make_hub()
    with hub:
        s = hub.distance_sensor("B")
        sim.distance = 3
        assert s.is_near(4) and not s.is_near(3) and not s.is_near(2)
        assert s.is_far(2) and not s.is_far(3) and not s.is_far(4)


def test_threshold_validation():
    hub, sim = make_hub()
    with hub:
        s = hub.distance_sensor("B")
        for bad in (-1, 11, float("nan"), float("inf")):
            with pytest.raises(ValueError):
                s.is_near(bad)
        for bad in (True, "3", None):
            with pytest.raises(TypeError):
                s.is_far(bad)
        assert s.is_near(10) in (True, False)            # bounds are accepted
        assert s.is_far(0) in (True, False)


def test_no_initial_value_times_out():
    hub, sim = make_hub(silent_sensors=True)
    with hub:
        with pytest.raises(OperationTimeout):
            hub.distance_sensor("B").read()


def test_sensor_removed_from_port():
    hub, sim = make_hub()
    with hub:
        s = hub.distance_sensor("B")
        assert s.read() == 0
        sim.detach("B")
        from helpers import wait_for
        assert wait_for(lambda: "B" not in hub.ports)
        with pytest.raises(DeviceNotFoundError):
            s.read()


def test_link_loss_raises_hub_disconnected():
    hub, sim = make_hub()
    with hub:
        s = hub.distance_sensor("B")
        assert s.read() == 0
        sim.drop_link()
        with pytest.raises(HubDisconnectedError):
            s.read()
