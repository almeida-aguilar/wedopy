"""UUID helpers for the WeDo 2.0 hub and the standard Bluetooth base."""
import binascii

HUB_SUFFIX = "-1212-efde-1523-785feabcd123"
STD_SUFFIX = "-0000-1000-8000-00805f9b34fb"


def hub_uuid(short):
    """128-bit UUID in the WeDo hub base for a 16-bit short UUID."""
    return "0000%04x%s" % (short, HUB_SUFFIX)


def std_uuid(short):
    """128-bit UUID in the standard Bluetooth base for a 16-bit short UUID."""
    return "0000%04x%s" % (short, STD_SUFFIX)


def normalize_uuid(text):
    """Accept ``0x1523``, ``1523`` or a full UUID; return canonical lowercase 128-bit form."""
    s = str(text).strip().lower()
    if s.startswith("0x"):
        s = s[2:]
    if "-" not in s and len(s) <= 8:
        try:
            n = int(s, 16)
        except ValueError:
            raise ValueError("invalid UUID %r" % s) from None
        return "%08x%s" % (n, STD_SUFFIX)
    c = s.replace("-", "")
    try:
        binascii.unhexlify(c)
    except (binascii.Error, ValueError):
        raise ValueError("invalid UUID %r" % s) from None
    if len(c) != 32:
        raise ValueError("invalid UUID %r" % s)
    return "%s-%s-%s-%s-%s" % (c[:8], c[8:12], c[12:16], c[16:20], c[20:])
