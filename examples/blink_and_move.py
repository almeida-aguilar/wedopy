"""Blink the LED while a motor runs, using cooperative tasks (no threads, no asyncio)."""
from wedopy import Hub, task

with Hub() as hub:
    def blink():
        while True:
            hub.led.index(6)
            yield task.sleep(0.3)
            hub.led.index(9)
            yield task.sleep(0.3)

    def move():
        motor = hub.motor("A")
        try:                      # cancelling a task never stops the motor by itself
            motor.run(75)
            yield task.sleep(3)
        finally:
            motor.stop()

    hub.tasks.add(blink, background=True)   # does not keep wait() alive
    hub.tasks.add(move)
    hub.tasks.wait()                        # returns when move() ends; blink is cancelled
