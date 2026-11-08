"""Shared helpers: a fast Timing profile and ready-made simulated hubs."""
import time

from wedopy import Hub
from wedopy_core.runtime.timing import Timing
from wedopy_core.transport.simulated import SimulatedHub

FAST = Timing(
    heartbeat_interval=0.05,
    watchdog_timeout=0.3,
    emergency_attempt_timeout=0.1,
    op_timeout=0.2,
    sensor_timeout=0.3,
    settle_quiet=0.12,
    settle_max=1.0,
    connect_timeout=2.0,
    poll=0.01,
)


def make_hub(devices=None, timing=FAST, **sim_kwargs):
    sim = SimulatedHub(devices, external_delay=0.03, **sim_kwargs)
    hub = Hub(transport=sim, timing=timing)
    return hub, sim


def wait_for(predicate, timeout=2.0, step=0.01):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return True
        time.sleep(step)
    return predicate()


class FakeClock:
    """Deterministic clock for the task scheduler: sleeping just advances time."""

    def __init__(self):
        self.now = 100.0
        self.slept = []

    def __call__(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds
