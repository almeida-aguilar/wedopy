"""Timing parameters (spec sections 5.1, 5.3 and 10). Initial values; tune with hardware tests."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Timing:
    heartbeat_interval: float = 0.5       # Battery read period while a motor is running
    watchdog_timeout: float = 2.0         # no valid ACK for this long -> emergency stop
    emergency_attempts: int = 2
    emergency_attempt_timeout: float = 0.5
    op_timeout: float = 1.0               # per-operation bound; also the max wait before an
                                          # emergency request can run (single writer, no abort)
    sensor_timeout: float = 1.0           # wait for the first value after configuring a sensor
    settle_quiet: float = 1.5             # connect(): no new/different port events for this long
    settle_max: float = 5.0               # connect(): hard cap on port discovery
    connect_timeout: float = 15.0         # scan + connect + service discovery
    poll: float = 0.02                    # watchdog loop period
