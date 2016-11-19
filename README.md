# IluAlarm
A home-made smart alarm clock created using a raspberry pi 2

## Introduction

This project was named after my girlfriend, as it is born as a
christmas present for her.

Here is a picture of the only working "IluAlarm" (so far)


The idea was to have a programmable alarm clock, and a music player,
and something to download stuff from the internet without keeping her
laptop always on. Oh, and also watch the downloaded things directly on
the TV!

Alarms can be added and updated using the dedicated android app, which
can also be used to change the device's color and adjust the volume.
A custom message can also be set to be shown on the device's display.

I actually wanted to create a Ionic app so it could also run on IOs
and other mobile phones but I had the idea too close to christmas so
no time for doing that. Maybe in the future!

It consists in a Raspberry PI 2 with a ST7565 display attached, some
RGB leds and a 3w amplifier with a couple of small speakers.

What can it do?

- Change color

- Play music (If you have Spotify Premium you can play your playlists!)

- Wake you up or remember you something (it also syncs with your Google Calendar!)

- Download torrents

- Be connected to a display

- Run Kodi (aka XBMC)

- And much more! It's a raspberry pi 2, so almost everything you can thing of.

## About the software

Everything has been written in Python, however some external software has been used.

- The alarm part, as well as the RGB leds and the display are
  controlled by a custom python script (start from raspberry/ilualarm2.py)

- Music (and Spotify integration) is handled by Mopidy (https://www.mopidy.com/)

- As media center it uses Kodi

- For downloading torrents it uses transmission

- For playing the alarm sounds it uses mplayer (yeha yeha, Python has
  some built-in things for that, but they didn't work ootb and I had
  VERY little time for completing everying)

The main contribution to the world of this project is the ST7565
python interface (See raspberry/st7565.py or raspberry/display.py).
It can also render custom fonts (See the raspberry/fonts/ directory)



## About the hardware

Materials used:

- Graphic ST7565 Positive LCD (128x64) with RGB backlight (https://www.adafruit.com/product/250)

- Some common-cathode RGB Leds (http://www.robot-italy.com/it/led-rgb-clear-25pcs-common-cathode.html)

- A 3.7w amplifier (http://www.robot-italy.com/it/amplificatore-stereo-3-7w-classe-d-max98306.html)

- A couple of 3w speakers (http://www.robot-italy.com/it/stereo-enclosed-speaker-set-3w-4-ohm.html)

- An arcade-game like button (for snoozing or stopping the alarm)

- A bunch of 3904 transistors

- Some resistors


And here is the electronic part schematics (TODO)

