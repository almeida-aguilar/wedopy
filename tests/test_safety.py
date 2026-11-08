import logging
import threading
import time

import pytest
from helpers import make_hub, wait_for

from wedopy import HubDisconnectedError, task
from wedopy_core import _wedopy as core
from wedopy_core.protocol import constants as K


class Capture(logging.Handler):
    def __init__(self):
        super().__init__(logging.DEBUG)
        self.messages = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def capture_watchdog_log():
    handler = Capture()
    log = logging.getLogger("wedopy.watchdog")
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    return log, handler


def test_watchdog_stops_motors_when_heartbeat_fails_but_writes_work():
    log, cap = capture_watchdog_log()
    try:
        hub, sim = make_hub()
        hub.connect()
        try:
            hub.motor("A").run(60)
            assert sim.motors[1] == 60
            sim.fail_reads = True                       # heartbeat (Battery read) now fails
            assert wait_for(lambda: hub._session.core.state is core.HubState.ERROR, 3.0)
            assert sim.motors[1] == 0                   # emergency stop reached the hub
            assert any("motors stopped" in m for m in cap.messages)
            assert any("stop attempt 1 ACK" in m for m in cap.messages)
        finally:
            hub.disconnect()
    finally:
        log.removeHandler(cap)


def test_watchdog_reports_unconfirmed_stop_when_hub_stops_answering():
    log, cap = capture_watchdog_log()
    try:
        hub, sim = make_hub()
        hub.connect()
        try:
            hub.motor("A").run(60)
            sim.freeze()
            assert wait_for(lambda: hub._session.core.state is core.HubState.ERROR, 4.0)
            assert any("stop NOT confirmed (2 attempts)" in m for m in cap.messages)
            sim.unfreeze()
            with pytest.raises(HubDisconnectedError):
                hub.motor("A").run(10)                  # errors are explicit, nothing is hidden
        finally:
            hub.disconnect()
    finally:
        log.removeHandler(cap)


def test_no_heartbeat_traffic_while_motors_are_stopped():
    hub, sim = make_hub()
    with hub:
        time.sleep(0.4)
        assert K.CHAR_BATTERY not in sim.reads
        hub.motor("A").run(20)
        assert wait_for(lambda: K.CHAR_BATTERY in sim.reads, 1.0)
        hub.motor("A").stop()


def test_watchdog_does_not_depend_on_the_task_scheduler():
    hub, sim = make_hub()
    hub.connect()
    seen = []

    def blocker():
        hub.motor("A").run(50)
        sim.fail_reads = True
        time.sleep(1.0)                                 # blocks every task: no yield
        seen.append(sim.motors[1])                      # the watchdog acted meanwhile
        yield task.yield_now()

    hub.tasks.add(blocker)
    hub.tasks.wait()
    try:
        assert seen == [0]
        assert hub._session.core.state is core.HubState.ERROR
    finally:
        hub.disconnect()


def test_link_loss_goes_to_error_and_every_operation_fails_explicitly():
    hub, sim = make_hub({"A": "motor", "B": "distance"})
    hub.connect()
    motor = hub.motor("A")
    motor.run(50)
    sim.drop_link()
    assert wait_for(lambda: hub._session.core.state is core.HubState.ERROR)
    assert not hub.is_connected
    with pytest.raises(HubDisconnectedError):
        motor.run(10)
    with pytest.raises(HubDisconnectedError):
        hub.led.on()
    with pytest.raises(HubDisconnectedError):
        hub.button.is_pressed
    hub.disconnect()                                    # cleans up a failed connection, no exception
    assert hub._session.core.state is core.HubState.DISCONNECTED


def test_disconnect_with_a_silent_hub_reports_unconfirmed_stop():
    hub, sim = make_hub()
    hub.connect()
    hub.motor("A").run(50)
    sim.freeze()
    hub._session.tasks.cancel()
    confirmed = hub._session.core.disconnect()
    assert confirmed is False
    assert hub._session.core.state is core.HubState.DISCONNECTED


def test_emergency_requests_run_before_queued_normal_ones():
    hub, sim = make_hub()
    with hub:
        c = hub._session.core
        order = []
        started, release = threading.Event(), threading.Event()

        def blocker():
            started.set()
            release.wait(2.0)
            order.append("blocker")

        reqs = [c._enqueue(blocker, needs_connected=False)]
        assert started.wait(1.0)
        reqs.append(c._enqueue(lambda: order.append("n1"), needs_connected=False))
        reqs.append(c._enqueue(lambda: order.append("n2"), needs_connected=False))
        reqs.append(c._enqueue(lambda: order.append("emergency"), emergency=True, needs_connected=False))
        release.set()
        for r in reqs:
            assert r.done.wait(2.0)
        assert order == ["blocker", "emergency", "n1", "n2"]


def test_single_writer_serialises_concurrent_callers():
    hub, sim = make_hub({"A": "motor", "B": "motor"}, ack_delay=0.005)
    with hub:
        errors = []

        def spam(port, speed):
            try:
                for _ in range(10):
                    hub.motor(port).run(speed)
            except Exception as exc:                    # pragma: no cover
                errors.append(exc)

        threads = [threading.Thread(target=spam, args=("A", 10)), threading.Thread(target=spam, args=("B", 20))]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        assert len(sim.writes_to(K.CHAR_OUTPUT_CMD)) == 20


def test_stop_all_keeps_going_after_one_failure_and_reports_it():
    hub, sim = make_hub({"A": "motor", "B": "motor"})
    with hub:
        hub.motor("A").run(30)
        hub.motor("B").run(30)
        original = sim.write

        def flaky(uuid, data, timeout):
            if uuid == K.CHAR_OUTPUT_CMD and data[0] == K.CONN_PORT_A:
                raise core.BLEError("simulated write failure")
            return original(uuid, data, timeout)

        sim.write = flaky
        with pytest.raises(core.BLEError):
            hub.stop_all()
        assert sim.motors[2] == 0                       # B was still stopped
        sim.write = original


def test_invalid_state_transition_is_rejected():
    c = core.Coordinator(make_hub()[1])
    with pytest.raises(core.InvalidStateError):
        c._set_state(core.HubState.CONNECTED)           # disconnected -> connected is not allowed
