import time
import settings
import random

if settings.ON_RASPBERRY:
    import RPi.GPIO as GPIO

class Button(object):

    def __init__(self, pin, listener=None):
        self.pin = pin
        self.listener = listener

        if settings.ON_RASPBERRY:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.last_press = None
        return

    def set_listener(self, listener):
        self.listener = listener
        return

    def loop(self, now):

        if settings.ON_RASPBERRY:
            if not GPIO.input(self.pin):
                if self.last_press is None:
                    if self.listener:
                        self.listener.press_start()
                    self.last_press = now
                else:
                    if self.listener:
                        self.listener.pressing(now - self.last_press)
                pass
            elif self.last_press is not None:
                if self.listener:
                    self.listener.press_end(now - self.last_press)
                self.last_press = None
                pass
        else:

            if self.last_press is None:
                # 1/1000 chance of pressing and releasing..
                coin = random.randint(0, 1000) == 0
                if coin:
                    if self.listener: self.listener.press_start()
                    self.last_press = now
                else:
                    if self.listener:
                        self.listener.pressing(now - self.last_press)
            else:
                # 1/100 chance of pressing and releasing..
                coin = random.randint(0, 100) == 0
                if coin:
                    if self.listener: self.listener.press_end(now - self.last_press)
                    self.last_press = None

        return

    pass
