import sys
import signal
import os
import json
import time
import ConfigParser
import functools
import datetime
import random
import dateutil.parser
from collections import namedtuple
import itertools

# IluAlarm imports
import settings
import rgb
import display
import button
import json_server as jserver
import fonts
import google
import common
import sound

if settings.ON_RASPBERRY:
    import alsaaudio
    import RPi.GPIO as GPIO
    #import pygame.mixer

CONFIG_VERSION = 38

R = 22
G = 24
B = 23

LCD_CS = 2
LCD_RST  = 3
LCD_A0 = 4
LCD_CLK = 27
LCD_SI = 17

BUTTON = 18

LOOP_GOOGLE_SYNC = 0
LOOP_COMMANDS = 1
LOOP_MESSAGES = 2
LOOP_HM = 3
LOOP_SEC = 4
LOOP_CONFIG = 5
LOOP_ROTATION = 6
LOOP_BG_ALARM_MODE = 7
LOOP_BUTTON = 8
LOOP_ALARMS = 9
LOOP_DISPLAY_CONTROLLER = 10
LOOP_WELCOME = 11
LOOP_VOLUME = 12

GMAIL_OAUTH_CLIENT_ID =  "1079384164251-61gtnku7mpa4n61u0e8lrmrc2krh9pck.apps.googleusercontent.com"
GMAIL_OAUTH_CLIENT_SECRET = "0PD2AenaP7DrkDr2yRakOEnV"

Hardware = namedtuple('Hardware', ['background', 'display', 'button'])
LoopBundle = namedtuple('LoopBundle', ['config', 'communication',
                                       'hardware', 'loop_handler'])

class Loop(object):

    def __init__(self, id, func, interval, condition, data=None, expires=None):
        self.id = id
        self.func = func
        self.interval = interval
        self.condition = condition
        self.last = None
        self.data = data or {}
        self.expires = expires
        return

    def get_elapsed_millis(self, now):
        diff = now - self.last
        return (diff.seconds * 1000) + (diff.microseconds / 1000)

    pass

class LoopHandler(object):

    def __init__(self, config, communication, hardware):
        self.priority = set()
        self.loops = []
        self.config = config
        self.hardware = hardware
        self.communication = communication
        self.bundle = LoopBundle(config, communication, hardware, self)
        self.force_recall = False
        return

    # interval is in millis
    def add_loop(self, id, func, interval=0, condition=None,
                 data=None, priority=False, expires=None):
        self.loops.append(Loop(id, func, interval, condition,
                               data=data, expires=expires))
        if priority:
            self.priority.add(id)

    def remove_loop(self, id):
        self.loops = [l for l in self.loops if l.id != id]

    def force_loop(self):
        self.force_recall = True

    def loop(self):
        remove_loops = set()

        has_priority = len(self.priority) > 0

        for loop in self.loops:
            now = datetime.datetime.now()
            
            if loop.expires is not None and now >= timeout.expires:
                # loop is expired.. remove it
                remove_loops.add(loop.id)
                continue

            if has_priority and loop.id not in self.priority:
                # There is a priority loop.. execute it first.
                continue

            if loop.condition is None or loop.condition():
                if self.force_recall \
                   or loop.interval == 0 \
                   or loop.last is None \
                   or loop.get_elapsed_millis(now) >= loop.interval:
                    loop.last = now
                    if loop.func(self.bundle, now, loop.data):
                        print "Loop completed"
                        remove_loops.add(loop.id)
                    pass
                pass
            pass

        if len(remove_loops) > 0:
            self.loops = [l for l in self.loops if l.id not in remove_loops]
            self.priority -= remove_loops

        self.force_recall = False
        return True

class SnoozeButtonListener(object):

    def __init__(self, com):
        self.com = com
        pass

    def press_start(self):
        return

    def pressing(self, delta):
        if delta >= datetime.timedelta(seconds=1):
            self.com.msg_to_gpio(common.Message.STOP)
    
    def press_end(self, delta):
        if delta < datetime.timedelta(seconds=1):
            self.com.msg_to_gpio(common.Message.SNOOZE, data=10)
        return

class AlarmRGB(rgb.RGB):

    def __init__(self, red, green, blue, start_color=None):
        rgb.RGB.__init__(self, red, green, blue)
        self.orig_color = (0, 0, 0)
        if start_color:
            self.set_color(*start_color)
        return

    def set_color(self, R, G, B):
        rgb.RGB.set_color(self, R, G, B)
        self.orig_color = (R, G, B)
        return

    def loop_alarm_mode(self, bundle, now, data):
        if bundle.config.has_playing_alarms():
            data['alarm_mode'] = True
            rgb.RGB.set_color(self,
                              random.randint(0, 255),
                              random.randint(0, 255),
                              random.randint(0, 255))
            pass
        else:
            # Not playing? if we were in alarm mode, re-set the color..
            if data.get('alarm_mode', False):
                data['alarm_mode'] = False
                rgb.RGB.set_color(self, *self.orig_color)

        pass
    pass


class AlarmDisplay(display.RGBDisplay):

    def __init__(self, LCD_CS, LCD_RST, LCD_A0, LCD_CLK, LCD_SI):
        display.RGBDisplay.__init__(self, LCD_CS, LCD_RST, LCD_A0, LCD_CLK, LCD_SI)
        
        self.rotating = []
        self.next_rot_id = 0

        self.volume = 0
        self.volume_mode = None
        return

    def small_text(self, x, y, text):
        self.lcd_ascii168_string(x, y, text)
        return

    def text(self, x, y, text, font):
        if settings.ON_RASPBERRY:
            return self.lcd_font_string(x, y, text, font)
        print "[DISPLAY]", x, y, text
        return len(text)

    def _set_status(self, _char):
        self.lcd_area_clear(5, 0, 3, 15)
        self.text(5, 0, _char, fonts.webdings.Webdings14)

    def _set_right_status(self, _char):
        self.lcd_area_clear(112, 0, 2, 15)
        if _char:
            self.text(112, 0, _char, fonts.webdings.Webdings14)
        
    def set_status_syncing(self):
        self._set_status("q")
            
    def set_status_ok(self):
        self._set_status("a")
        
    def set_status_error(self):
        self._set_status("r")

    def set_status_has_alarms(self, has_alarms=True):    
        self._set_right_status("X" if has_alarms else None)            
        
    def add_rotating_text(self, text):
        rotating = [self.next_rot_id, 0, text]
        self.next_rot_id += 1
        self.rotating.append(rotating)
        return rotating

    def set_rotating_text(self, rotating, text):
        rotating[2] = text
        return

    def del_rotating_text(self, rotating):
        self.rotating = [r
                         for r in self.rotating
                         if r[0] != rotating[0]]

        if not self.rotating:
            self.lcd_area_clear(5, 4, 4, 123)
            pass

        return

    def show_volume(self, now, volume):
        self.volume = volume
        self.volume_mode = now
        return
    
    def set_default_text(self, text):
        self.default_text = text

    def get_default_text(self):
        return self.default_text
        
    def _get_timer_str(self, now, alarm):
        missing_seconds = alarm.get_missing_time(now).seconds
        return (str(alarm) +
                " %02d:%02d" % (missing_seconds // 60, missing_seconds % 60))

    def _rotate(self, strg, n):
        return strg[n:] + strg[:n]

    def loop_controller(self, bundle, now, data):
        # 1. If there is any alarm playing, show their
        #    names rotating on the lower half of the display.
        #    Skip everything else..
        # 2. If there is a timer alarm active (not yet elapsed), show
        #    it's name and its' missing time (mm:ss)

        known = data.get('known', None)
        if known is None:
            known = {}
            data['known'] = known

        alarms = bundle.config.get_enabled_alarms()
        
        disable = set(k for k in known)
        has_alarms = False
        
        for a in alarms:
            is_known = a.id in known
            if a.is_playing():
                if not is_known:
                    # A new alarm is playing! add it to the list of known,
                    # And add it's text
                    rot = self.add_rotating_text(str(a))
                    known[a.id] = (a, rot)
                else:
                    # this was probably snoozed..
                    d = known[a.id]
                    self.set_rotating_text(d[1], str(a))
            else:
                if a.is_timer() or a.is_snoozed():
                    _str = self._get_timer_str(now, a)

                    if a.is_snoozed():
                        _str = "snz. " + _str + " . . . . . "

                    # new timer alarm.. Add a rotating text
                    # that will update
                    if not is_known:
                        rot = self.add_rotating_text(_str)
                        known[a.id] = (a, rot)
                    else:
                        d = known[a.id]
                        self.set_rotating_text(d[1], _str)
                else:                    
                    continue  # Don't remove the alarm from the
                              # disable set..
                    
            if is_known:
                disable.remove(a.id)
            pass

        for d in disable:
            # This alarm was playing but it
            # has probably been stopped..
            self.del_rotating_text(known[d][1])
            del known[d]

        has_alarms = any(True for a in bundle.config.get_enabled_alarms())
            
        had_alarms = data.get('had_alarms', False)
            
        if had_alarms != has_alarms:
            bundle.hardware.display.set_status_has_alarms(has_alarms=has_alarms)
            data['had_alarms'] = has_alarms
            pass
            
        return

    def loop_volume(self, bundle, now, data):        
        if self.volume_mode is not None:
            if (now - self.volume_mode).seconds >= 2:
                self.lcd_area_clear(0, 4, 4, 128)
                self.volume_mode = None
                del data['volume']
            else:
                vol = data.get('volume', None)
                if vol is None:
                    self.lcd_area_clear(0, 4, 4, 128)
                    font = fonts.tahoma.Tahoma12
                    w = self.get_font_width("VOLUME", font)
                    self.text((128 - w) // 2, 4, "VOLUME", font)

                if vol is None or vol != self.volume:
                    self.lcd_area_clear(0, 6, 2, 128)
                    _str = "Volume " + str(self.volume)

                    font = fonts.tahoma.Tahoma10
                    wpipes = self.get_font_width("|", font)

                    # assuming volume 0..100
                    pipes = int((self.volume / wpipes) * 0.55)
                    _str = "|" * pipes
                    self.text(9, 6, _str, font)

                    data['volume'] = self.volume
        return
    
    def loop_rotation(self, bundle, now, data):
        # Skip if doing something else..
        if self.volume_mode is not None:
            return
        
        _str = ("   ".join(r[2] for r in self.rotating)
                if len(self.rotating) > 0
                else self.default_text)
        w = self.get_font_width(_str, fonts.tahoma.Tahoma22)

        # Don't rotate if there is enough space..
        if w <= 128:
            last_str = data.get('last_str', None)

            if last_str is None or last_str != _str:
                self.lcd_area_clear(0, 4, 4, 128)
                data['last_str'] = _str
            self.text((128 - w) // 2, 4, _str, fonts.tahoma.Tahoma22)
        else:
            # If we go in "non rotating mode" (w <= 128), screen needs
            # to be cleared..
            data['last_str'] = None

            string = _str + "    "
            last_idx = data.get('last_idx', 0)
            rotated = self._rotate(string, last_idx)
            data['last_idx'] = (last_idx + 1) % len(string)

            self.lcd_area_clear(0, 4, 4, 128)

            chars = 5
            while chars < len(rotated):
                w = self.get_font_width(rotated[:chars],
                                        fonts.tahoma.Tahoma22)
                if w >= 118: break
                chars += 1
                pass                
            self.text(5, 4, rotated[:chars], fonts.tahoma.Tahoma22)
        #else:
        #    w = self.get_font_width(str("J"), fonts.wingdings.Wingdings)
        #    self.text((128 - w) // 2, 5, "J", fonts.wingdings.Wingdings)
        return

    def loop_time_hm(self, bundle, now, data):
        date_time = datetime.datetime.strftime(now, '%H:%M')
        last_time = data.get("last_time", None)

        if last_time is None or last_time != date_time:
            self.lcd_area_clear(25, 0, 4, 80)
            w = self.get_font_width(str(date_time), fonts.tahoma.Tahoma26)
            self.text((128 - w) // 2, 0, str(date_time), fonts.tahoma.Tahoma26)
            data['last_time'] = date_time

        return

    def loop_time_sec(self, bundle, now, data):
        date = datetime.datetime.strftime(now, '%S')
        last_date = data.get("last_date", None)

        if last_date is None or last_date != date:
            self.lcd_area_clear(105, 2, 2, 23)
            self.text(105, 2, str(date), fonts.tahoma.Tahoma12)
            data['last_date'] = date

        return
    pass


def loop_sync_google_calendar(bundle, now, data):
    bundle.hardware.display.set_status_syncing()
    try:
        evs = google.get_upcoming_events(now)

        existing_ids = set(a.tag
                           for a in bundle.config.get_alarms())

        for e in evs:
            if e[0] not in existing_ids:
                bundle.config.create_scheduled_alarm(e[1],
                                                     name="Google sched " + e[2],
                                                     message=e[2], tag=e[0])
        bundle.hardware.display.set_status_ok()
    except Exception as e:
        print e
        bundle.hardware.display.set_status_error()

    return


def loop_welcome(bundle, now, data):
    hw = bundle.hardware
    
    gen = data.get('rgb', None)

    if gen is None:        
        hw.display.text(3, 3, "ILUALARM", fonts.tahoma.Tahoma22)
        to_color = bundle.config.get_color()    
        gen = itertools.chain(hw.background.fade_gen((0, 0, 0), to_color, 20))
        data['rgb'] = gen
        
    try:
        hw.background.set_color(*next(gen))
    except:
        hw.display.lcd_clear()
        to_color = bundle.config.get_color()    
        hw.background.set_color(*to_color)

        text = bundle.config.get("text")
        hw.display.set_default_text(text)
        
        return True  # end of fade..
    
    return


def _msg_snooze(now, msg_data, bundle):
    active = bundle.config.get_playing_alarms()
    if active:
        snooze_for = (msg_data or 10)
        for a in active:
            a.snooze(now, time=snooze_for)
            
        bundle.config.notify_update()
        
        if settings.ON_RASPBERRY:
            sound.stop_alarm_sound()
    return


def _msg_stop(now, msg_data, bundle):
    active = bundle.config.get_playing_alarms()
    if active:
        for a in active:
            a.stop(now)

        bundle.config.notify_update()

        if settings.ON_RASPBERRY:
            sound.stop_alarm_sound()
    return


def _msg_color(now, msg_data, bundle):
    red, green, blue = msg_data
    bundle.hardware.background.set_color(red, green, blue)
    bundle.config.set_color((red, green, blue))

def _msg_text(now, msg_data, bundle):
    bundle.hardware.display.set_default_text(msg_data)
    bundle.config.set('text', msg_data)

def _msg_volume(now, msg_data, bundle):
    mixer = alsaaudio.Mixer(alsaaudio.mixers()[0])
    mixer.setvolume(50 + (int(msg_data) // 2))
    bundle.config.set('volume', int(msg_data))
    bundle.hardware.display.show_volume(now, int(msg_data))
    
__check_msg_exec_map = {
    common.Message.SNOOZE: _msg_snooze,
    common.Message.STOP: _msg_stop,
    common.Message.COLOR: _msg_color,
    common.Message.TEXT_168: _msg_text,
    common.Message.VOLUME: _msg_volume,
}

def loop_check_messages(bundle, now, data):
    bundle.communication.pop_gpio_msg_exec(now, __check_msg_exec_map, bundle)
    return

def _cmd_get_color(now, data, bundle):
    c = bundle.config.get_color()
    return { 'r' : c[0], 'g' : c[1], 'b' : c[2]}

def _cmd_get_volume(now, data, bundle):
    mixer = alsaaudio.Mixer(alsaaudio.mixers()[0])
    return mixer.getvolume()

def _cmd_get_text(now, data, bundle):
    c = bundle.config.get('text')
    return c

def _cmd_add_alarm(now, data, bundle):
    c = bundle.config
    
    try:
        print "ADDING ALARM"
        if data['type'] == common.Alarm.TYPE_SCHEDULED:
            date = dateutil.parser.parse(data['time'])
            res = c.create_scheduled_alarm(date,
                                           name=data.get('name'),
                                           message=data.get('message'),
                                           repeat_every=data.get('repeat_every'))
            print res
            if res: return res.to_json()
        elif data['type'] == common.Alarm.TYPE_TIMER:
            res = c.create_timer_alarm(now,
                                       data['timeout'],
                                       name=data.get('name'),
                                       message=data.get('message'))
            if res: return res.to_json()

        return None
    except Exception as e:
        print e
        return None

def _cmd_edit_alarm(now, data, bundle):
    def _cnt_valid(alarm, data, attr):
        if attr in data and data[attr] is not None:
            setattr(alarm, attr, data[attr])
    
    alarm_id = data['id']

    alarm = bundle.config.find_alarm(alarm_id)

    if alarm is None:
        print "Alarm", alarm_id, "not found"
        return None

    if 'time' in data and data['time'] is not None:
        date = dateutil.parser.parse(data['time'])
        alarm.time = date
        alarm.set_time = date
        
    if 'set_time' in data and data['set_time'] is not None:
        date = dateutil.parser.parse(data['set_time'])
        alarm.set_time = date
    
    _cnt_valid(alarm, data, 'enabled')
    _cnt_valid(alarm, data, 'repeat_every')
    _cnt_valid(alarm, data, 'message')
    _cnt_valid(alarm, data, 'timeout')

    if alarm.is_timer() and 'timeout' in data:
        alarm.time = now + datetime.timedelta(seconds=data['timeout'])
        alarm.set_time = alarm.time
    
    return alarm.to_json()
    

def _cmd_quit(now, data, bundle):
    return "bye"


__check_cmd_exec_map = {
    "alarm_list" : lambda n, d, b: [a.to_json()
                                    for a in b.config.get_alarms()],
    "color" : _cmd_get_color,
    "create_alarm" : _cmd_add_alarm,
    "edit_alarm" : _cmd_edit_alarm,
    "quit" : _cmd_quit,
    "text" : _cmd_get_text,
    "volume": _cmd_get_volume,
}

def loop_check_commands(bundle, now, data):
    bundle.communication.pop_gpio_cmd_exec(now, __check_cmd_exec_map, bundle)


def loop_save_config(bundle, now, data):
    print "Saving config.."
    bundle.config.save()


def loop_alarms(bundle, now, data):
    for a in bundle.config.get_enabled_alarms():
        
        # if alarm is not playing but should, make it play..
        if not a.is_playing() and a.should_play(now):
            a.play(now)
            sound.play_alarm_sound()

        # Is it playing? Check if it should be snoozed for timeout...
        elif a.is_playing():
            timeout = bundle.config.get('snooze_timeout')
            if a.is_snooze_timeout(now, timeout=timeout):
                a.snooze(now, time=bundle.config.get('snooze'))
                sound.stop_alarm_sound()
    return


def gpio_process(communication):

    config = common.Config()

    if settings.ON_RASPBERRY:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        mixer = alsaaudio.Mixer(alsaaudio.mixers()[0])
        mixer.setvolume(50 + (config.get_volume() // 2))
        pass

    hw = Hardware(AlarmRGB(R, G, B),
                  AlarmDisplay(LCD_CS, LCD_RST, LCD_A0, LCD_CLK, LCD_SI),
                  button.Button(BUTTON, listener=SnoozeButtonListener(communication)))

    loop_handler = LoopHandler(config, communication, hw)    
    
    # NOTE: ADD ORDER MATTERS!
    
    loop_handler.add_loop(LOOP_WELCOME, loop_welcome,
                          interval=100, priority=True)

    # Check if the button is pressed..
    loop_handler.add_loop(LOOP_BUTTON, lambda b, n, d: hw.button.loop(n))
            
    # Display: Hour + minutes handling.
    loop_handler.add_loop(LOOP_HM, hw.display.loop_time_hm,
                          interval=500)

    # Display: Seconds handling
    loop_handler.add_loop(LOOP_SEC, hw.display.loop_time_sec,
                          interval=100, data={})

    # Check for messages from the server
    loop_handler.add_loop(LOOP_MESSAGES, loop_check_messages)

    # Check for commands from the server
    loop_handler.add_loop(LOOP_COMMANDS, loop_check_commands)
    
    # Check for alarms
    loop_handler.add_loop(LOOP_ALARMS, loop_alarms, interval=200)

    #  Display: controller
    loop_handler.add_loop(LOOP_DISPLAY_CONTROLLER, hw.display.loop_controller,
                          interval=400)

    # Display: Volume
    loop_handler.add_loop(LOOP_VOLUME, hw.display.loop_volume,
                          interval=30)

    # Display: Lower screen text
    loop_handler.add_loop(LOOP_ROTATION, hw.display.loop_rotation,
                          interval=700)

    # Background: alarm mode color change
    loop_handler.add_loop(LOOP_BG_ALARM_MODE, hw.background.loop_alarm_mode,
                          interval=500)

    # Config: save every min..
    loop_handler.add_loop(LOOP_CONFIG, loop_save_config, interval=60000)

    # Check for calendar updates periodically..
    loop_handler.add_loop(LOOP_GOOGLE_SYNC, loop_sync_google_calendar,
                          interval=600000)

    while True:

        if not loop_handler.loop():
            break

        time.sleep(0.02)
        pass # while True

    return
