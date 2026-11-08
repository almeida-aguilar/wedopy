import pytest
from helpers import FakeClock, make_hub

from wedopy import InvalidStateError, task
from wedopy.tasks import TaskManager
from wedopy_core.protocol import constants as K


def manager(on_interrupt=None):
    clock = FakeClock()
    return TaskManager(clock=clock, sleeper=clock.sleep, on_interrupt=on_interrupt), clock


def test_registration_order_is_the_tie_break():
    tm, clock = manager()
    log = []

    def make(name):
        def t():
            log.append(name + "1")
            yield task.yield_now()
            log.append(name + "2")
        return t

    for n in "abc":
        tm.add(make(n))
    assert tm.wait() is None
    assert log == ["a1", "b1", "c1", "a2", "b2", "c2"]


def test_sleep_lets_other_tasks_run_and_orders_by_due_time():
    tm, clock = manager()
    log = []

    def slow():
        yield task.sleep(0.3)
        log.append("slow")

    def fast():
        yield task.sleep(0.1)
        log.append("fast")
        yield task.sleep(0.1)
        log.append("fast2")

    tm.add(slow)
    tm.add(fast)
    tm.wait()
    assert log == ["fast", "fast2", "slow"]
    assert abs(sum(clock.slept) - 0.3) < 1e-9
    assert all(s > 0 for s in clock.slept)


def test_plain_function_is_a_one_step_task_and_args_use_partial():
    import functools
    tm, _ = manager()
    log = []
    tm.add(lambda: log.append("lambda"))
    tm.add(functools.partial(log.append, "partial"))
    tm.wait()
    assert log == ["lambda", "partial"]


def test_background_tasks_do_not_keep_wait_alive_and_are_cancelled():
    tm, clock = manager()
    log = []

    def blink():
        try:
            while True:
                log.append("tick")
                yield task.sleep(0.3)
        finally:
            log.append("blink closed")

    def move():
        log.append("move start")
        yield task.sleep(1.0)
        log.append("move end")

    tm.add(blink, background=True)
    tm.add(move)
    tm.wait()
    assert log[0] == "tick" and log[-1] == "blink closed"
    assert "move end" in log
    assert log.count("tick") == 4                      # t = 0, 0.3, 0.6, 0.9


def test_wait_without_normal_tasks_returns_at_once_and_cancels_background():
    tm, clock = manager()
    ran = []
    tm.add(lambda: ran.append(1), background=True)
    assert tm.wait() is None
    assert ran == [] and clock.slept == []
    assert tm.wait() is None                           # manager is empty and reusable


def test_manager_is_reusable_after_wait():
    tm, _ = manager()
    log = []
    tm.add(lambda: log.append(1))
    tm.wait()
    tm.add(lambda: log.append(2))
    tm.wait()
    assert log == [1, 2]


def test_task_can_add_tasks_while_running():
    tm, _ = manager()
    log = []

    def child():
        log.append("child")

    def parent():
        log.append("parent")
        tm.add(child)
        yield task.yield_now()
        log.append("parent end")

    tm.add(parent)
    tm.wait()
    assert log == ["parent", "child", "parent end"]


def test_error_cancels_the_rest_runs_finally_and_reraises_original():
    tm, _ = manager()
    log = []

    def worker():
        try:
            while True:
                yield task.sleep(0.5)
        finally:
            log.append("worker cleaned")

    def bad():
        yield task.sleep(0.2)
        raise ValueError("boom")

    tm.add(worker)
    tm.add(bad)
    with pytest.raises(ValueError) as info:
        tm.wait()
    assert str(info.value) == "boom"
    assert log == ["worker cleaned"]
    notes = getattr(info.value, "__notes__", None)
    if notes is not None:
        assert any("'bad'" in n for n in notes)
    tm.add(lambda: log.append("again"))                 # still usable
    tm.wait()
    assert log[-1] == "again"


def test_invalid_yield_raises_typeerror_inside_the_task():
    tm, _ = manager()
    seen = []

    def t():
        try:
            yield 1
        except TypeError as exc:
            seen.append(str(exc))
        yield task.yield_now()
        seen.append("continued")

    tm.add(t)
    tm.wait()
    assert "task.sleep" in seen[0] and seen[1] == "continued"


def test_bare_yield_is_rejected():
    tm, _ = manager()

    def t():
        yield

    tm.add(t)
    with pytest.raises(TypeError):
        tm.wait()


def test_async_functions_and_non_callables_are_rejected():
    tm, _ = manager()

    async def coro():
        pass

    with pytest.raises(TypeError):
        tm.add(coro)
    with pytest.raises(TypeError):
        tm.add(42)
    with pytest.raises(TypeError):
        tm.add(lambda: None, True)                     # background is keyword-only


def test_sleep_validation():
    for bad in (True, "1", None):
        with pytest.raises(TypeError):
            task.sleep(bad)
    for bad in (-1, float("nan"), float("inf")):
        with pytest.raises(ValueError):
            task.sleep(bad)
    assert type(task.sleep(0)) is type(task.yield_now())


def test_instruction_never_yielded_warns():
    with pytest.warns(RuntimeWarning):
        task.sleep(1)


def test_wait_from_a_task_is_invalid():
    tm, _ = manager()

    def t():
        tm.wait()
        yield task.yield_now()

    tm.add(t)
    with pytest.raises(InvalidStateError):
        tm.wait()


def test_cancel_from_a_task_closes_others_now_and_itself_at_next_yield():
    tm, _ = manager()
    log = []

    def other():
        try:
            yield task.sleep(5)
        finally:
            log.append("other closed")

    def canceller():
        yield task.sleep(0.1)
        log.append("cancelling")
        tm.cancel()
        log.append("after cancel")
        try:
            yield task.sleep(1)
        finally:
            log.append("canceller closed")
        log.append("never")

    tm.add(other)
    tm.add(canceller)
    tm.wait()
    assert log == ["cancelling", "other closed", "after cancel", "canceller closed"]


def test_cancel_before_wait_means_nothing_runs():
    tm, clock = manager()
    ran = []
    tm.add(lambda: ran.append(1))
    tm.cancel()
    tm.cancel()                                        # idempotent
    tm.wait()
    assert ran == []


def test_cleanup_that_yields_is_recorded_as_an_error_not_raised_by_wait():
    tm, _ = manager()

    def greedy():
        try:
            yield task.sleep(1)
        finally:
            yield task.yield_now()                      # not allowed during cleanup

    def killer():
        yield task.sleep(0.1)
        tm.cancel()
        yield task.yield_now()

    tm.add(greedy)
    tm.add(killer)
    tm.wait()
    assert len(tm.diagnostics) == 1
    assert isinstance(tm.diagnostics[0][1], RuntimeError)


def test_keyboard_interrupt_cancels_runs_finally_and_calls_handler():
    calls = []
    clock = FakeClock()

    def sleeper(seconds):
        raise KeyboardInterrupt

    tm = TaskManager(clock=clock, sleeper=sleeper, on_interrupt=lambda: calls.append("stop motors"))
    log = []

    def t():
        try:
            yield task.sleep(1)
        finally:
            log.append("finally ran")

    tm.add(t)
    with pytest.raises(KeyboardInterrupt):
        tm.wait()
    assert log == ["finally ran"] and calls == ["stop motors"]


# ---- with a hub ------------------------------------------------------------------


def test_led_and_motor_run_concurrently_on_a_hub():
    hub, sim = make_hub()
    with hub:
        def blink():
            while True:
                hub.led.index(6)
                yield task.sleep(0.02)
                hub.led.index(9)
                yield task.sleep(0.02)

        def move():
            motor = hub.motor("A")
            try:
                motor.run(75)
                yield task.sleep(0.2)
            finally:
                motor.stop()

        hub.tasks.add(blink, background=True)
        hub.tasks.add(move)
        hub.tasks.wait()
        leds = [w for w in sim.writes_to(K.CHAR_OUTPUT_CMD) if w[0] == K.CONN_RGB]
        assert len(leds) >= 4
        assert sim.motors[1] == 0


def test_cancel_does_not_stop_motors_but_finally_does():
    hub, sim = make_hub()
    with hub:
        def careless():
            hub.motor("A").run(40)
            yield task.sleep(5)

        hub.tasks.add(careless)
        hub.tasks.add(lambda: hub.tasks.cancel())
        hub.tasks.wait()
        assert sim.motors[1] == 40                      # cancel() leaves hardware alone
        hub.stop_all()
        assert sim.motors[1] == 0


def test_disconnect_cancels_tasks_before_stopping_motors():
    hub, sim = make_hub()
    hub.connect()

    def mover():
        motor = hub.motor("A")
        try:
            motor.run(60)
            yield task.sleep(5)
        finally:
            motor.stop()                                # still allowed: runs before BLE closes

    def quitter():
        yield task.sleep(0.05)
        hub.disconnect()
        yield task.yield_now()

    hub.tasks.add(mover)
    hub.tasks.add(quitter)
    hub.tasks.wait()
    assert sim.motors[1] == 0
    assert not hub.is_connected
