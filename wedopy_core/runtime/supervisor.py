"""Process-level supervisor: best-effort cleanup if the program ends with a hub still connected."""
import atexit
import logging
import threading
import weakref

_log = logging.getLogger("wedopy.supervisor")


class Supervisor:
    def __init__(self):
        self._sessions = weakref.WeakSet()
        self._lock = threading.Lock()
        atexit.register(self.cleanup)

    def register(self, session):
        with self._lock:
            self._sessions.add(session)

    def unregister(self, session):
        with self._lock:
            self._sessions.discard(session)

    def cleanup(self):
        with self._lock:
            sessions = list(self._sessions)
        for session in sessions:
            try:
                session.emergency_close()
            except Exception:  # never raise from atexit
                _log.debug("emergency close failed", exc_info=True)


supervisor = Supervisor()
