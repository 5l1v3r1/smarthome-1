import time

import RPi.GPIO as GPIO

class MotionSensor:

    def __init__(self, pin):
        self._enabled = True
        self._pin = pin

        self._lastTriggered = 0

        # setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self._pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

    def enabled(self):
        return self._enabled

    def enable(self):
        self._enabled = True

    def disable(self):
        self._enabled = False

    def triggered(self):
        if not self.enabled(): return False

        curTime = time.time()

        if GPIO.input(self._pin) != 1:
            return False

        if curTime - self._lastTriggered > 150.0:
            self._lastTriggered = curTime
            return False

        return True


