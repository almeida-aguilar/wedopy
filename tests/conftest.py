"""Test bootstrap.

Uses the compiled ``wedopy_core._wedopy`` when it exists. Otherwise it executes the ``.pyx``
source as plain Python (the core is written in the Python-compatible subset of Cython) so the
suite runs without a compiler; a warning says so.
"""
import pathlib
import sys
import types
import warnings

ROOT = pathlib.Path(__file__).resolve().parent.parent
for p in (ROOT / "src", ROOT, ROOT / "tests"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

try:
    import wedopy_core._wedopy  # noqa: F401
except ImportError:
    import wedopy_core
    pyx = ROOT / "wedopy_core" / "_wedopy.pyx"
    mod = types.ModuleType("wedopy_core._wedopy")
    mod.__file__ = str(pyx)
    sys.modules["wedopy_core._wedopy"] = mod
    exec(compile(pyx.read_text(), str(pyx), "exec"), mod.__dict__)
    wedopy_core._wedopy = mod
    warnings.warn("wedopy_core._wedopy is not compiled; running the .pyx source as plain Python")

import struct
from wedopy_core.protocol import constants as K
from wedopy_core.transport.simulated import SimulatedHub

_orig_value_bytes = SimulatedHub._value_bytes


def _sim_value_bytes(self, conn):
    typ, mode = self.sensor_modes.get(conn, (None, None))
    if typ == K.TYPE_TILT and mode == K.TILT_ANGLE:
        return struct.pack("<bb", int(self.tilt_angle[0]), int(self.tilt_angle[1]))
    return _orig_value_bytes(self, conn)


SimulatedHub._value_bytes = _sim_value_bytes

