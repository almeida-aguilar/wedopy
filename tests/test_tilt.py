import pytest
from helpers import make_hub, wait_for

from wedopy import DeviceNotFoundError, HubDisconnectedError, OperationTimeout
from wedopy_core.protocol import constants as K


def hub_with_tilt():
    return make_hub({"A": "tilt", "B": "motor"})


def test_read_angle():
    hub, sim = hub_with_tilt()
    with hub:
        t = hub.tilt_sensor("A")
        sim.tilt_angle = (12, -30)
        x, y = t.read_angle()
        assert (x, y) == (12, -30)
        assert all(isinstance(v, int) for v in (x, y))
        # Angle mode needs the RAW unit (0x00); with SI (0x02) the hub
        # silently ignores the configuration and never notifies
        # (verified on hardware, Nov 2026).
        assert sim.writes_to(K.CHAR_INPUT_CMD)[0] == bytes.fromhex("0102012200010000000001")


def test_shake_beyond_nominal_range_is_not_clamped():
    hub, sim = hub_with_tilt()
    with hub:
        t = hub.tilt_sensor("A")
        sim.tilt_angle = (80, -77)
        assert t.read_angle() == (80, -77)


@pytest.mark.parametrize("name", ["neutral", "back", "right", "left", "forward"])
def test_read_direction(name):
    hub, sim = hub_with_tilt()
    with hub:
        t = hub.tilt_sensor("A")
        sim.tilt_code = {"neutral": 0, "back": 3, "right": 5, "left": 7, "forward": 9}[name]
        assert t.read_direction() == name
        # Direction keeps SI (0x02), which is what the hub honours for this mode.
        assert sim.writes_to(K.CHAR_INPUT_CMD)[0] == bytes.fromhex("0102012201010000000201")


def test_switching_between_modes_reconfigures_and_ignores_stale_values():
    hub, sim = hub_with_tilt()
    with hub:
        t = hub.tilt_sensor("A")
        sim.tilt_angle = (5, 6)
        sim.tilt_code = 9
        assert t.read_angle() == (5, 6)
        assert t.read_direction() == "forward"
        assert t.read_angle() == (5, 6)
        formats = [w for w in sim.writes_to(K.CHAR_INPUT_CMD) if w[:2] == b"\x01\x02"]
        assert [f[4] for f in formats] == [0, 1, 0]      # mode byte: angle, direction, angle
        sim.set_tilt_angle(-1, 2)
        assert t.read_angle() == (-1, 2)


def test_tilt_repr():
    hub, _ = hub_with_tilt()
    with hub:
        t = hub.tilt_sensor("A")
        assert repr(t) == "TiltSensor('A')"


def test_no_initial_value_times_out():
    hub, sim = make_hub({"A": "tilt", "B": "motor"}, silent_sensors=True)
    with hub:
        with pytest.raises(OperationTimeout):
            hub.tilt_sensor("A").read_angle()
        with pytest.raises(OperationTimeout):
            hub.tilt_sensor("A").read_direction()


def test_sensor_removed_from_port():
    hub, sim = hub_with_tilt()
    with hub:
        t = hub.tilt_sensor("A")
        sim.tilt_angle = (0, 0)
        assert t.read_angle() == (0, 0)
        sim.detach("A")
        assert wait_for(lambda: "A" not in hub.ports)
        with pytest.raises(DeviceNotFoundError):
            t.read_angle()


def test_link_loss_raises_hub_disconnected():
    hub, sim = hub_with_tilt()
    with hub:
        t = hub.tilt_sensor("A")
        sim.tilt_angle = (0, 0)
        assert t.read_angle() == (0, 0)
        sim.drop_link()
        with pytest.raises(HubDisconnectedError):
            t.read_angle()

