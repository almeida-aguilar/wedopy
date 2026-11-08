"""Cycle through the indexed LED colours, then show an RGB colour."""
import time

from wedopy import Hub

with Hub() as hub:
    for i in range(1, 11):
        hub.led.index(i)
        time.sleep(0.3)
    hub.led.rgb(255, 80, 0)
    time.sleep(1)
