"""Drive two motors together (A first, then B; not atomic), then stop."""
import time

from wedopy import Hub

with Hub() as hub:
    motors = hub.motors(("A", "B"))
    motors.run(75)
    time.sleep(2)
    motors.stop()
