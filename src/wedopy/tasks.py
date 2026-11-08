"""Cooperative task scheduler behind ``hub.tasks`` (spec 5.7).

Single thread (the one calling ``wait()``), deterministic order, switch only at ``yield``.
"""
import functools
import heapq
import inspect
import itertools
import logging
import time

from . import task as _task
from .exceptions import InvalidStateError

_log = logging.getLogger("wedopy.tasks")


def _name_of(func):
    while isinstance(func, functools.partial):
        func = func.func
    return getattr(func, "__name__", None) or repr(func)


class _Task:
    __slots__ = ("func", "name", "background", "gen", "due", "seq", "cancelled", "finished")

    def __init__(self, func, background):
        self.func = func
        self.name = _name_of(func)
        self.background = background
        self.gen = None
        self.due = 0.0
        self.seq = 0
        self.cancelled = False
        self.finished = False


class TaskManager:
    def __init__(self, *, clock=time.monotonic, sleeper=time.sleep, on_interrupt=None):
        self._clock = clock
        self._sleeper = sleeper
        self._on_interrupt = on_interrupt
        self._heap = []
        self._counter = itertools.count()
        self._normal = 0          # live non-background tasks (the running one included)
        self._running = None
        self._waiting = False
        self._failure = None
        self.diagnostics = []     # secondary errors of the last wait(): [(task name, exception)]

    # -- public API --------------------------------------------------------

    def add(self, func, *, background=False):
        """Register a task. It starts running inside :meth:`wait`. Returns ``None``."""
        if not callable(func):
            raise TypeError("a task must be a callable, not %s" % type(func).__name__)
        if inspect.iscoroutinefunction(func) or inspect.isasyncgenfunction(func):
            raise TypeError("'async def' tasks are not supported; use a plain function or a "
                            "generator that yields task.sleep(...)")
        if not isinstance(background, bool):
            raise TypeError("background must be True or False")
        t = _Task(func, background)
        t.due = self._clock()
        t.seq = next(self._counter)
        heapq.heappush(self._heap, (t.due, t.seq, t))
        if not background:
            self._normal += 1
        return None

    def wait(self):
        """Run tasks until every normal task has finished, then cancel background tasks."""
        if self._waiting or self._running is not None:
            raise InvalidStateError("wait() cannot be called from a task or during another wait()")
        self._waiting = True
        self.diagnostics = []
        try:
            self._loop()
        except KeyboardInterrupt:
            self.cancel()
            if self._on_interrupt is not None:
                try:
                    self._on_interrupt()
                except Exception:
                    _log.debug("interrupt handler failed", exc_info=True)
            raise
        finally:
            self._waiting = False
        failure, self._failure = self._failure, None
        if failure is not None:
            raise failure
        return None

    def cancel(self):
        """Close every task (normal and background). Does not stop motors."""
        entries, self._heap = self._heap, []
        for _due, _seq, t in sorted(entries):
            self._close(t)
            self._finish(t)
        if self._running is not None:
            self._running.cancelled = True   # closed at its next yield

    # -- internals ---------------------------------------------------------

    def _loop(self):
        while self._normal > 0 and self._failure is None:
            if not self._heap:
                break
            due = self._heap[0][0]
            delay = due - self._clock()
            if delay > 0:
                # Sleep with the task still queued, so an interrupt can cancel it cleanly.
                self._sleeper(delay)
                continue
            _due, _seq, t = heapq.heappop(self._heap)
            self._running = t
            try:
                self._advance(t)
            finally:
                self._running = None
        if self._failure is None:
            self._cancel_background()

    def _cancel_background(self):
        keep = []
        for entry in self._heap:
            t = entry[2]
            if t.background:
                self._close(t)
                self._finish(t)
            else:
                keep.append(entry)
        heapq.heapify(keep)
        self._heap = keep

    def _advance(self, t):
        throw = None
        while True:
            try:
                if t.gen is None:
                    result = t.func()
                    if inspect.isgenerator(result):
                        t.gen = result
                        instr = next(t.gen)
                    elif inspect.iscoroutine(result):
                        result.close()
                        raise TypeError("task %r returned a coroutine; 'async def' is not supported" % t.name)
                    else:
                        self._finish(t)
                        return
                elif throw is not None:
                    exc, throw = throw, None
                    instr = t.gen.throw(exc)
                else:
                    instr = next(t.gen)
            except StopIteration:
                self._finish(t)
                return
            except Exception as exc:
                self._fail(t, exc)
                return
            except BaseException:
                self._finish(t)
                raise
            if t.cancelled:
                if isinstance(instr, _task._Instruction):
                    instr._used = True
                self._close(t)
                self._finish(t)
                return
            if isinstance(instr, _task._Sleep):
                instr._used = True
                t.due = self._clock() + instr.seconds
            elif isinstance(instr, _task._YieldNow):
                instr._used = True
                t.due = self._clock()
            else:
                throw = TypeError("task %r yielded %r; tasks may only yield task.sleep(...) or "
                                  "task.yield_now()" % (t.name, instr))
                continue
            t.seq = next(self._counter)
            heapq.heappush(self._heap, (t.due, t.seq, t))
            return

    def _finish(self, t):
        if t.finished:
            return
        t.finished = True
        if not t.background:
            self._normal -= 1

    def _close(self, t):
        gen, t.gen = t.gen, None
        if gen is None:
            return
        try:
            gen.close()
        except Exception as exc:   # e.g. RuntimeError: the cleanup tried to yield
            _log.error("task %r failed while being cancelled: %r", t.name, exc)
            self.diagnostics.append((t.name, exc))

    def _fail(self, t, exc):
        self._finish(t)
        if self._failure is None:
            self._failure = exc
            if hasattr(exc, "add_note"):
                exc.add_note("raised in task %r" % t.name)
            _log.error("task %r failed: %r", t.name, exc)
            self.cancel_others(t)
        else:
            self.diagnostics.append((t.name, exc))

    def cancel_others(self, failed):
        entries, self._heap = self._heap, []
        for _due, _seq, other in sorted(entries):
            self._close(other)
            self._finish(other)
