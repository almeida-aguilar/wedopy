"""Protocol constants taken from the reference implementation and captures.

Payloads are native BLE ones (no BLED112 framing).
"""
from .uuid import hub_uuid, std_uuid

# Services
SERVICE_GAP = std_uuid(0x1800)
SERVICE_DEVICE_INFO = std_uuid(0x180A)
SERVICE_BATTERY = std_uuid(0x180F)
SERVICE_HUB = hub_uuid(0x1523)
SERVICE_IO = hub_uuid(0x4F0E)

# Standard characteristics
CHAR_BATTERY = std_uuid(0x2A19)

# Hub service 0x1523
CHAR_HUB_NAME = hub_uuid(0x1524)
CHAR_BUTTON = hub_uuid(0x1526)
CHAR_PORT = hub_uuid(0x1527)
CHAR_LOW_VOLTAGE = hub_uuid(0x1528)
CHAR_HIGH_CURRENT = hub_uuid(0x1529)
CHAR_LOW_SIGNAL = hub_uuid(0x152A)
CHAR_TURN_OFF = hub_uuid(0x152B)
CHAR_DISCONNECT = hub_uuid(0x152E)

# I/O service 0x4f0e
CHAR_SENSOR = hub_uuid(0x1560)
CHAR_FORMAT = hub_uuid(0x1561)
CHAR_INPUT_CMD = hub_uuid(0x1563)
CHAR_OUTPUT_CMD = hub_uuid(0x1565)

# Connect IDs
CONN_PORT_A = 0x01
CONN_PORT_B = 0x02
CONN_CURRENT = 0x03
CONN_VOLTAGE = 0x04
CONN_PIEZO = 0x05
CONN_RGB = 0x06

# Device type IDs
TYPE_MOTOR = 0x01
TYPE_VOLTAGE = 0x14
TYPE_CURRENT = 0x15
TYPE_PIEZO = 0x16
TYPE_RGB = 0x17
TYPE_TILT = 0x22
TYPE_MOTION = 0x23  # the "distance" sensor
TYPE_GENERIC = 0x24

# Units for the input format command
UNIT_RAW = 0
UNIT_PERCENT = 1
UNIT_SI = 2

# RGB LED modes
LED_ABSOLUTE = 0
LED_DISCRETE = 1

# Tilt modes (bump is not exposed)
TILT_ANGLE = 0
TILT_DIRECTION = 1

# Distance modes (count is not exposed)
DISTANCE_DETECT = 0

TYPE_NAMES = {
    TYPE_MOTOR: "motor",
    TYPE_VOLTAGE: "voltage",
    TYPE_CURRENT: "current",
    TYPE_PIEZO: "piezo",
    TYPE_RGB: "rgb-led",
    TYPE_TILT: "tilt",
    TYPE_MOTION: "distance",
    TYPE_GENERIC: "generic",
}

# Characteristics the hub must expose for wedopy to work.
REQUIRED_CHARS = (CHAR_BATTERY, CHAR_PORT, CHAR_SENSOR, CHAR_INPUT_CMD, CHAR_OUTPUT_CMD)
