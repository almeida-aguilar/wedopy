"""Drive until the distance sensor reports something nearer than 3 (scale 0..10)."""
import time

from wedopy import Hub, OperationTimeout

with Hub() as hub:
    sensor = hub.distance_sensor("B")
    motor = hub.motor("A")
    motor.run(70)
    while True:
        try:
            if sensor.is_near(3):
                break
        except OperationTimeout:
            print("no reading from the sensor; stopping")
            break
        time.sleep(0.05)
    motor.stop()
