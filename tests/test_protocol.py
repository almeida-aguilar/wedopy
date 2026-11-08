from wedopy_core import _wedopy as core
from wedopy_core.protocol import constants as K
from wedopy_core.protocol.uuid import normalize_uuid


def test_command_vectors():
    # Vectors come from the BLED112 captures with the framing removed (spec 12.3).
    assert core.motor_power(1, -87) == bytes.fromhex("010101a9")
    assert core.motor_power(1, 500) == bytes((1, 1, 1, 100))
    assert core.motor_power(2, -500) == bytes((2, 1, 1, 0x9C))
    assert core.motor_power(1, 0) == bytes((1, 1, 1, 0))
    assert core.led_index(4) == bytes.fromhex("06040104")
    assert core.led_rgb(0, 0xFF, 0x40) == bytes.fromhex("06040300ff40")
    assert core.input_start(2) == bytes.fromhex("000102")
    assert core.input_start(1) == bytes.fromhex("000101")


def test_input_format_vectors():
    assert core.input_format(1, K.TYPE_TILT, 1, 1, K.UNIT_SI, True) == bytes.fromhex("0102012201010000000201")
    assert core.input_format(K.CONN_RGB, K.TYPE_RGB, K.LED_DISCRETE, 1, K.UNIT_RAW, True) == \
        bytes.fromhex("0102061701010000000001")


def test_parse_port_event():
    ev = core.parse_port_event(bytes([0x01, 0x01, 0x00, 0x22, 0, 0, 0, 0x10, 0, 0, 0, 0x10]))
    assert (ev.conn, ev.attached, ev.type) == (1, True, K.TYPE_TILT)
    ev = core.parse_port_event(bytes([0x02, 0x00]))
    assert (ev.conn, ev.attached) == (2, False)
    for bad in (b"\x01", b"", b"\x01\x01\x00"):
        try:
            core.parse_port_event(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError for %r" % bad)


def test_parse_sample_and_scalars():
    s = core.parse_sample(bytes([0x03, 0x02, 0x00, 0x00, 0xA0, 0x40]))
    assert s.conn == 2
    assert core.decode_scalar(s.value) == 5.0
    assert core.decode_scalar(b"\x07") == 7.0
    assert core.decode_scalar(b"\x01\x01") == 257.0
    try:
        core.decode_scalar(b"\x01\x02\x03")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_tilt_decoders():
    assert core.decode_tilt_angle(bytes([0xFB, 0x0A])) == (-5, 10)
    import struct
    assert core.decode_tilt_angle(struct.pack("<ff", 12.4, -30.6)) == (12, -31)
    names = {0: "neutral", 3: "back", 5: "right", 7: "left", 9: "forward"}
    for code, name in names.items():
        assert core.tilt_direction_name(struct.pack("<f", float(code))) == name
    assert core.tilt_direction_name(struct.pack("<f", 4.0)) == "unknown"


def test_normalize_uuid():
    assert normalize_uuid("0x1523") == "00001523-0000-1000-8000-00805f9b34fb"
    assert normalize_uuid("2A19") == "00002a19-0000-1000-8000-00805f9b34fb"
    assert normalize_uuid(K.SERVICE_HUB) == K.SERVICE_HUB
    assert K.SERVICE_HUB == "00001523-1212-efde-1523-785feabcd123"
    for bad in ("zz", "1234-5678", ""):
        try:
            normalize_uuid(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("expected ValueError for %r" % bad)
