import pytest
from helpers import make_hub

from wedopy_core.protocol import constants as K


def test_run_and_stop_write_expected_bytes():
    hub, sim = make_hub()
    with hub:
        m = hub.motor("A")
        m.run(100)
        m.run(-87)
        m.stop()
        assert sim.writes_to(K.CHAR_OUTPUT_CMD) == [
            bytes.fromhex("01010164"), bytes.fromhex("010101a9"), bytes.fromhex("01010100")]


def test_run_zero_is_stop():
    hub, sim = make_hub()
    with hub:
        m = hub.motor("A")
        m.run(70)
        m.run(0)
        assert sim.motors[1] == 0


@pytest.mark.parametrize("bad", [101, -101, 1000])
def test_out_of_range_rejected(bad):
    hub, sim = make_hub()
    with hub:
        with pytest.raises(ValueError):
            hub.motor("A").run(bad)


@pytest.mark.parametrize("bad", [50.5, 100.0, True, False, "50", None])
def test_wrong_types_rejected(bad):
    hub, sim = make_hub()
    with hub:
        with pytest.raises(TypeError):
            hub.motor("A").run(bad)
    assert not sim.writes_to(K.CHAR_OUTPUT_CMD) or sim.motors.get(1, 0) == 0


def test_group_runs_in_order_a_then_b():
    hub, sim = make_hub({"A": "motor", "B": "motor"})
    with hub:
        g = hub.motors(("B", "A"))              # given out of order on purpose
        g.run(75)
        assert sim.writes_to(K.CHAR_OUTPUT_CMD)[:2] == [bytes((1, 1, 1, 75)), bytes((2, 1, 1, 75))]
        g.stop()
        assert sim.motors == {1: 0, 2: 0}


def test_group_argument_validation():
    hub, sim = make_hub({"A": "motor", "B": "motor"})
    with hub:
        with pytest.raises(TypeError):
            hub.motors("AB")
        with pytest.raises(ValueError):
            hub.motors(())
        with pytest.raises(ValueError):
            hub.motors(("A", "A"))


def test_stop_all_stops_every_motor():
    hub, sim = make_hub({"A": "motor", "B": "motor"})
    with hub:
        hub.motor("A").run(30)
        hub.motor("B").run(-30)
        hub.stop_all()
        assert sim.motors == {1: 0, 2: 0}
