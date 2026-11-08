"""Small educational time helper. Use the standard ``time`` module for everything else."""
import time as _time

_START = _time.monotonic()


def running_time():
    """Milliseconds since ``wedopy`` was imported (the program's start, in practice)."""
    return int((_time.monotonic() - _START) * 1000)
