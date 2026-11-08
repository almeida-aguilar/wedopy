"""Run motor A for two seconds."""
import time

from wedopy import Hub

with Hub() as hub:
    motor = hub.motor("A")
    motor.run(100)
    time.sleep(2)
    motor.stop()
