ON_RASPBERRY = True

try:
    import RPi.GPIO as GPIO
except Exception:
    ON_RASPBERRY = False

DEBUG = False

MOPIDY_CONF = "/home/mariotti/.config/mopidy/mopidy.conf"
