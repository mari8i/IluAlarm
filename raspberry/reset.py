R = 22
G = 23
B = 24

LCD_CS = 2
LCD_RST  = 3
LCD_A0 = 4
LCD_CLK = 27
LCD_SI = 17

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

for c in (R, G, B, LCD_CS, LCD_RST, LCD_A0, LCD_CLK, LCD_SI):
    GPIO.setup(c, GPIO.OUT)

GPIO.cleanup()
