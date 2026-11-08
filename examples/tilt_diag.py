import time
from wedopy import Hub
from wedopy_core.protocol import constants as K
from wedopy_core import _wedopy as core

_orig = core.Coordinator._on_notify
def _patched(self, uuid, data):
    if uuid == K.CHAR_SENSOR:
        print(f"NOTIFY conn={data[1]:02x} value={data[2:].hex()} len={len(data)-2}")
    return _orig(self, uuid, data)
core.Coordinator._on_notify = _patched

with Hub() as hub:
    t = hub.tilt_sensor("A")
    print(">>> mueve el sensor en X e Y por separado <<<")
    for i in range(15):
        raw = hub._session.core.read_sensor(
            t._conn, K.TYPE_TILT, K.TILT_ANGLE, K.UNIT_RAW,
            expected_len=None, timeout=3.0,
        )
        print(f"[{i}] raw={raw.hex()} len={len(raw)}")
        time.sleep(1)
