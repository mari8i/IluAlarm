import settings
import numpy as np

if settings.ON_RASPBERRY:
    import RPi.GPIO as GPIO


ILARIA = (2, 130, 132)

class RGB(object):

    def __init__(self, red, green, blue):
        
        self.red = red
        self.green = green
        self.blue = blue

        if settings.ON_RASPBERRY:
            for c in (red, green, blue):
                GPIO.setup(c, GPIO.OUT)

            self.rfade = GPIO.PWM(red, 100)
            self.rfade.start(0)
            self.gfade = GPIO.PWM(green, 100)
            self.gfade.start(0)        
            self.bfade = GPIO.PWM(blue, 100)
            self.bfade.start(0)
        pass

    def normalize_color(self, code):
        return code * 100 / 255

    def set_color(self, r, g, b):
        if settings.ON_RASPBERRY:        
            self.rfade.ChangeDutyCycle(self.normalize_color(r))
            self.gfade.ChangeDutyCycle(self.normalize_color(g))
            self.bfade.ChangeDutyCycle(self.normalize_color(b))
        else:
            print "[RGB]", r, g, b
        return    

    def fade(self, from_color, to_color, percent):
        '''assumes color is rgb between (0, 0, 0) and (255, 255, 255)'''
        from_color = np.array(from_color)
        to_color = np.array(to_color)
        vector = to_color - from_color
        return from_color + vector * percent
    
    def fade_gen(self, from_color, to_color, samples):
        '''assumes color is rgb between (0, 0, 0) and (255, 255, 255),
        div is integer (e.g. 1000 = 1000 samples)'''

        p = 0.0
        d = 1.0 / samples

        from_color = np.array(from_color)
        to_color = np.array(to_color)
        vector = to_color - from_color

        for x in xrange(samples):
            yield from_color + vector * p
            p += d
    
    pass 
