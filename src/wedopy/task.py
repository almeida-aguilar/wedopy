"""Scheduling instructions for cooperative tasks (spec 5.7).

    yield task.sleep(0.3)
    yield task.yield_now()

These are general instructions and do not depend on any hub; ``hub.tasks`` runs them.
"""
import math
import warnings

__all__ = ["sleep", "yield_now"]


class _Instruction:
    """Base class. A created-but-never-yielded instruction warns, like an un-awaited coroutine."""

    _label = "instruction"

    def __init__(self):
        self._used = False

    def __del__(self):
        if not getattr(self, "_used", True):
            warnings.warn("task.%s() was created but never yielded; write 'yield task.%s()'"
                          % (self._label, self._label), RuntimeWarning, stacklevel=2)


class _Sleep(_Instruction):
    _label = "sleep"

    def __init__(self, seconds):
        super().__init__()
        self.seconds = seconds

    def __repr__(self):
        return "task.sleep(%r)" % (self.seconds,)


class _YieldNow(_Instruction):
    _label = "yield_now"

    def __repr__(self):
        return "task.yield_now()"


def yield_now():
    """Move the current task to the end of the ready queue without pausing it."""
    return _YieldNow()


def sleep(seconds):
    """Suspend the current task for at least ``seconds`` while other tasks keep running."""
    if isinstance(seconds, bool) or not isinstance(seconds, (int, float)):
        raise TypeError("seconds must be a number, not %s" % type(seconds).__name__)
    if math.isnan(seconds) or math.isinf(seconds) or seconds < 0:
        raise ValueError("seconds must be a finite number >= 0, got %r" % (seconds,))
    if seconds == 0:
        return _YieldNow()
    return _Sleep(float(seconds))
