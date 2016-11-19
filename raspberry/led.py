import RPi.GPIO as GPIO
import time
import random
import rgb
import display

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

R = 22
G = 23
B = 24

LCD_CS = 2
LCD_RST  = 3
LCD_A0 = 4
LCD_CLK = 27
LCD_SI = 17


leds = rgb.RGB(R, G, B)
leds.set_color(*rgb.ILARIA)

d = display.RGBDisplay(2, 3, 4, 27, 17)
   
d.lcd_ascii168_string(2,2,"RIGA 1")
d.lcd_ascii168_string(2,4,"RIGA 2")
d.lcd_ascii168_string(2,6,"RIGA 3")

time.sleep(20)

# for f in (rfade, gfade, bfade):
#     for x in xrange(100):
#         i = x / 100.0
#         f.ChangeDutyCycle(100.0 * i)
#         time.sleep(0.1)
#         f.ChangeDutyCycle(0)

i = 0
while True:
    leds.set_color(random.randint(0, 255),
                   random.randint(0, 255),
                   random.randint(0, 255))
    d.lcd_ascii168_string(2, 0,"HAHA " + str(i))
    i += 1
    time.sleep(1)
    pass


GPIO.cleanup()
