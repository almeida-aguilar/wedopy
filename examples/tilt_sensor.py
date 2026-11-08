"""Print the tilt angle and direction."""
import time
from wedopy import Hub

with Hub() as hub:
    tilt = hub.tilt_sensor("A")
    for _ in range(20):
        print("angle", tilt.read_angle(), "| direction", tilt.read_direction())
        time.sleep(0.25)
