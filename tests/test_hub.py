import pytest
from helpers import FAST, make_hub, wait_for

from wedopy import (AmbiguousDeviceError, DeviceNotFoundError, DeviceTypeError, Hub,
                    HubConnectionError, InvalidStateError)
from wedopy_core import _wedopy as core
from wedopy_core.protocol import constants as K


def test_construction_does_not_connect():
    hub, sim = make_hub()
    assert not hub.is_connected
    assert not sim.connected
    assert hub.ports == {}


def test_connect_discovers_ports_and_returns_self():
    hub, sim = make_hub({"A": "motor", "B": "distance"})
    assert hub.connect() is hub
    try:
        assert hub.is_connected
        assert hub.ports == {"A": "motor", "B": "distance"}   # internal devices are not listed
    finally:
        hub.disconnect()


def test_ports_is_a_copy():
    hub, sim = make_hub()
    with hub:
        snap = hub.ports
        snap["A"] = "bogus"
        assert hub.ports["A"] == "motor"


def test_duplicate_port_events_keep_configured_mode():
    hub, sim = make_hub({"A": "motor", "B": "distance"}, repeat_ports=0.03)
    with hub:
        sensor = hub.distance_sensor("B")
        sim.set_distance(4)
        assert sensor.read() == 4
        n = len(sim.writes_to(K.CHAR_INPUT_CMD))
        import time
        time.sleep(0.2)                        # several identical port events arrive
        assert sensor.read() == 4
        assert len(sim.writes_to(K.CHAR_INPUT_CMD)) == n


def test_device_attached_later_appears_in_snapshot():
    hub, sim = make_hub({"A": "motor"})
    with hub:
        assert "B" not in hub.ports
        sim.attach("B", "tilt")
        assert wait_for(lambda: hub.ports.get("B") == "tilt")
        sim.detach("B")
        assert wait_for(lambda: "B" not in hub.ports)


def test_context_manager_stops_motors_and_closes():
    hub, sim = make_hub()
    with hub:
        hub.motor("A").run(50)
        assert sim.motors[1] == 50
    assert sim.motors[1] == 0
    assert not sim.connected
    assert not hub.is_connected


def test_context_manager_does_not_mask_original_error():
    hub, sim = make_hub()
    with pytest.raises(KeyError):
        with hub:
            raise KeyError("boom")
    assert not sim.connected


def test_disconnect_twice_is_fine():
    hub, sim = make_hub()
    hub.connect()
    hub.disconnect()
    hub.disconnect()
    assert not hub.is_connected


def test_selection_rules():
    hub, sim = make_hub({"A": "motor", "B": "motor"})
    with hub:
        with pytest.raises(AmbiguousDeviceError):
            hub.motor()
        assert hub.motor("A").port == "A"
        assert hub.motor("b").port == "B"
        with pytest.raises(DeviceNotFoundError):
            hub.distance_sensor()
        with pytest.raises(ValueError):
            hub.motor("C")
        with pytest.raises(TypeError):
            hub.motor(1)


def test_single_candidate_is_selected_and_wrong_type_is_reported():
    hub, sim = make_hub({"A": "motor", "B": "distance"})
    with hub:
        assert hub.motor().port == "A"
        assert hub.distance_sensor().port == "B"
        with pytest.raises(DeviceTypeError):
            hub.motor("B")
        with pytest.raises(DeviceNotFoundError):
            hub.tilt_sensor()


def test_empty_port_is_device_not_found():
    hub, sim = make_hub({"A": "motor"})
    with hub:
        with pytest.raises(DeviceNotFoundError):
            hub.motor("B")


def test_operations_before_connect_raise_invalid_state():
    hub, sim = make_hub()
    with pytest.raises(InvalidStateError):
        hub.motor("A")
    with pytest.raises(InvalidStateError):
        hub.led.on()
    with pytest.raises(InvalidStateError):
        hub.stop_all()


def test_connect_failure_and_recovery():
    hub, sim = make_hub(fail_connect=True)
    with pytest.raises(HubConnectionError):
        hub.connect()
    assert not hub.is_connected
    assert hub._session.core.state is core.HubState.ERROR
    sim.fail_connect = False
    hub.connect()                               # connect() recovers a hub in error state
    try:
        assert hub.is_connected
    finally:
        hub.disconnect()


def test_wrong_device_is_rejected():
    hub, sim = make_hub()
    sim.has_characteristic = lambda uuid: False
    with pytest.raises(HubConnectionError):
        hub.connect()


def test_optional_disconnect_notification_is_tolerated():
    hub, sim = make_hub()
    assert sim.supports_disconnect_notify is False
    with hub:
        assert hub.is_connected


def test_shutdown_declares_hub_off_only_after_ack():
    hub, sim = make_hub()
    hub.connect()
    hub.shutdown()
    assert sim.writes_to(K.CHAR_TURN_OFF) == [b"\x01"]
    assert hub._session.core.state is core.HubState.SHUTDOWN
    with pytest.raises(InvalidStateError):
        hub.motor("A")
    hub.disconnect()
    assert hub._session.core.state is core.HubState.DISCONNECTED


def test_refresh_ports_replays_devices():
    hub, sim = make_hub({"A": "motor", "B": "tilt"})
    with hub:
        assert hub.refresh_ports() == {"A": "motor", "B": "tilt"}
