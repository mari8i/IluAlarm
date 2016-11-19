import multiprocessing
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
import alsaaudio
import subprocess

# IluAlarm imports
import settings
import rgb
import display
import button
import json_server as jserver
import fonts
import google

if settings.ON_RASPBERRY:
    import RPi.GPIO as GPIO
    #import pygame.mixer


CONFIG_VERSION = 38

DEBUG = False

GMAIL_OAUTH_CLIENT_ID =  "1079384164251-61gtnku7mpa4n61u0e8lrmrc2krh9pck.apps.googleusercontent.com"
GMAIL_OAUTH_CLIENT_SECRET = "0PD2AenaP7DrkDr2yRakOEnV"


def read_config():
    defaults = {
        "version" : CONFIG_VERSION,
        "alarms" : [],
        "start-color" : rgb.ILARIA,
        "volume" : 80,
    }

    try:
        with open("config.json", "r") as fc:
            saved = json.load(fc)

            if not saved['version'] or saved['version'] < CONFIG_VERSION:
                print "Config file upgrade.. resetting"
                write_config(defaults, Alarm.ALARM_POOL)
            else:
                defaults.update(saved)
            pass
    except Exception as e:
        print e
        print "Creating config file.."
        write_config(defaults, [])
        pass

    defaults['alarms'] = [Alarm.from_json(pa)
                          for pa in defaults['alarms']]

    return defaults

def write_config(config, alarms):
    dump = dict(config)

    dump['alarms'] = [a.to_json()
                      for a in alarms]

    with open("config.json", "w") as fc:
        print dump
        json.dump(dump, fc)
        pass
    pass

current_sound_process = None

def play_alarm_sound():
    return
    
    global current_sound_process
    
    if current_sound_process is not None:
        print "PROCESS SOUND ALRESADY RUNNING..."
        return
        
    current_sound_process = \
        subprocess.Popen(["mplayer", "-loop", "0",
                          '/home/pi/ilualarm_devel/buzzer_alarm.wav'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
    #pygame.mixer.init(48000, -16, 1, 1024)
    #pygame.mixer.music.load('/home/pi/ilualarm_devel/buzzer_alarm.wav')
    #pygame.mixer.music.set_volume(config['volume'])
    #pygame.mixer.music.play(-1)
    return
    
def stop_alarm_sound():
    global current_sound_process
    
    if current_sound_process is not None:
        current_sound_process.terminate()
        current_sound_process = None
    #pygame.mixer.music.stop()
    #pygame.mixer.music.quit()
    return
    

"""
    Features:
    . Google calendar
    . Custom alarm clock
    . Custom bg + display color


    Settings:
    . Spotify
    .

    Define the rest APIs
    Base response:
    {
      status: [0, 1, 2, 3, ...],
    }

    . set_color(r, g, b)
      Sets the led color and background display color.

    . snooze()
      Tells the ilualarm to shut up.

    . settings_spotify(username, password)
      Sets the spotify account

    . set_text(text, timeout)
      Sets the given text for the given time on the display.

    SW:
    pip install --upgrade google-api-python-client

"""

R = 22
G = 24
B = 23

LCD_CS = 2
LCD_RST  = 3
LCD_A0 = 4
LCD_CLK = 27
LCD_SI = 17

BUTTON = 18


# indexes used for timings array
DELAY_TIME = 0


class Message(object):

    SNOOZE = 0
    TEXT_168 = 1
    COLOR = 2
    STOP = 3

    def __init__(self, _type, data=None):
        self.type = _type
        self.data = data
        return

    pass

class Alarm(object):

    
    ALARM_POOL = set()

    TYPE_SCHEDULED = 0
    TYPE_TIMER = 1

    has_timer = False

    # Type of alarms
    # 1. once at a certain date
    # 2. starting from a date, every N hours repeated.
    # 3. Timer

    # TODO Ideas:
    # Alarm that when snoozed goes to the next message
    # Example usage: when doing a receip that has a sequence of timings
    
    def __init__(self, type, time, id=None, name=None,
                 message=None, enabled=True, tag=None):
        if id:
            if any(id == a.id for a in Alarm.ALARM_POOL):
                raise Exception("ID ALREADY IN POOL")
            self.id = id
        else:
            self.id = len(Alarm.ALARM_POOL) + 1

        Alarm.ALARM_POOL.add(self)

        self.tag = tag
        self.type = type
        self.name = name
        if not self.name:
            self.name = "ALARM " + str(self.id)

        Alarm.has_timer = any(a.type == Alarm.TYPE_TIMER
                              for a in Alarm.ALARM_POOL)


        if DEBUG:
            print "Created alarm", self.id, self.name

        self.set_time = time
        self.time = time
        self.snoozed = False
        self.message = message
        self.enabled = enabled
        self.playing = False
        return

    @staticmethod
    def create_scheduled_alarm(start_time, name=None,
                               message=None, repeat_every=None,
                               id=None, tag=None):
        """
        repeat_every is in minutes
        """
        a = Alarm(Alarm.TYPE_SCHEDULED, start_time, id=id,
                  name=name, message=message, tag=tag)

        a.repeat_every = repeat_every

        return a

    @staticmethod
    def create_timer_alarm(now, timeout, name=None,
                           message=None, id=None, tag=None):
        """
        timeout is in seconds
        """
        a = Alarm(Alarm.TYPE_TIMER,
                  now + datetime.timedelta(seconds=timeout),
                  id=id, name=name, message=message, tag=tag)

        a.timeout = timeout

        return a

    @staticmethod
    def from_json(json):
        # type, time, id=None, name=None, message=None, enabled=True
        a = Alarm(json['type'],
                  dateutil.parser.parse(json['time']),
                  name=json['name'],
                  id=json['id'],
                  message=json['message'],
                  enabled=json['enabled'])

        a.set_time = dateutil.parser.parse(json['set_time'])
        if a.type == Alarm.TYPE_TIMER:
            a.timeout = json['timeout']
        elif a.type == Alarm.TYPE_SCHEDULED:
            a.repeat_every = json['repeat_every']
        return a

    @staticmethod
    def loop(now, config, background, front_display):
        for a in Alarm.ALARM_POOL:
            if not a.playing and a.should_play(now):
                a.play()
                background.start_alarm_mode(now)
                front_display.start_alarm_mode(now, a)

                if settings.ON_RASPBERRY:
                    play_alarm_sound()
                break

    @staticmethod
    def get_playing_alarms():
        return set((a
                    for a in Alarm.ALARM_POOL
                    if a.playing))

    def get_missing_time(self, now):
        return self.time - now
    
    def snooze(self, now, time=1):
        """
        time is in minutes
        """

        self.time = now + datetime.timedelta(minutes=time)
        self.snoozed = True
        self.playing = False
        return

    def stop(self, now):
        print "Stopping alarm"

        if self.type == Alarm.TYPE_SCHEDULED and self.repeat_every is not None:
            self.time += datetime.timedelta(minutes=self.repeat_every)
            return True
        else:
            self.time = None

        self.playing = False

        return False

    def should_play(self, now):
        # Alarm not enabled.. well.. skip
        if not self.enabled:
            return False

        # Start time is set and time has passed..
        if self.time and self.time < now:
            return True

        return False

    def play(self):
        self.playing = True
        self.snoozed = False
        return

    def to_json(self):
        res = {
            "id" : self.id,
            "type" : self.type,
            "name" : self.name,
            "set_time" : self.set_time.isoformat(),
            "time" : self.time.isoformat() if self.time else None,
            "message" : self.message,
            "enabled" : self.enabled,
        }

        if self.type == Alarm.TYPE_SCHEDULED:
            res['repeat_every'] = self.repeat_every
        elif self.type == Alarm.TYPE_TIMER:
            res['timeout'] = self.timeout

        return res

    def __str__(self):
        return "[ALARM] " + str(self.id) + " " + str(self.time)

    pass

class SnoozeButtonListener(object):

    def __init__(self, gpio_queue):
        self.queue = gpio_queue
        pass

    def press_start(self):
        return

    def press_end(self, delta):
        print delta, datetime.timedelta(seconds=1)
        if delta < datetime.timedelta(seconds=1):
            self.queue.put(Message(Message.SNOOZE, data=1))
        else:
            self.queue.put(Message(Message.STOP))
        return

class AlarmRGB(rgb.RGB):

    def __init__(self, red, green, blue):
        rgb.RGB.__init__(self, red, green, blue)
        self.alarm_mode = False
        self.alarm_time = 0
        self.orig_color = (red, green, blue)
        return

    def start_alarm_mode(self, now, timeout=None):
        self.alarm_mode = True
        self.alarm_time = now
        rgb.RGB.set_color(self,
                          random.randint(0, 255),
                          random.randint(0, 255),
                          random.randint(0, 255))
        return

    def set_color(self, R, G, B):
        rgb.RGB.set_color(self, R, G, B)
        self.orig_color = (R, G, B)
        return

    def stop_alarm_mode(self, now):
        self.alarm_mode = False
        self.alarm_time = 0
        rgb.RGB.set_color(self, *self.orig_color)
        pass

    def loop(self, now):

        if self.alarm_mode and (now - self.alarm_time).microseconds >= 500000:
            rgb.RGB.set_color(self,
                              random.randint(0, 255),
                              random.randint(0, 255),
                              random.randint(0, 255))
            self.alarm_time = now
            pass

        return

class AlarmDisplay(display.RGBDisplay):

    def __init__(self, LCD_CS, LCD_RST, LCD_A0, LCD_CLK, LCD_SI):
        display.RGBDisplay.__init__(self, LCD_CS, LCD_RST, LCD_A0, LCD_CLK, LCD_SI)
        self.alarm_mode = False
        self.alarm_time = 0
        self.last_update = None
        self.toggle = False

        self.last_date = None
        self.last_time = None

        self.counter = None
        self.rotating = []
        self.next_rot_id = 0
        self.rot_cache = None
        self.last_rot = None
        self.last_rot_str = None
        self.last_rot_idx = 0
        self.running_alarms = []
        return

    def small_text(self, x, y, text):
        #self.lcd_ascii168_string(x, y, text)
        self.lcd_ascii168_string(x, y, text)
        return
    
    def text(self, x, y, text, font):
        #self.lcd_ascii168_string(x, y, text)
        return self.lcd_font_string(x, y, text, font=font)

    def add_rotating_text(self, text):
        rotating = [self.next_rot_id, 0, text]
        self.next_rot_id += 1
        self.rotating.append(rotating)
        self.rot_cache = None  # invalidate cache
        return rotating

    def set_rotating_text(self, rotating, text):
        rotating[2] = text
        self.rot_cache = None  # invalidate cache
        return

    def del_rotating_text(self, rotating):
        self.rotating = [r
                         for r in self.rotating
                         if r[0] != rotating[0]]

        if not self.rotating:
            self.lcd_area_clear(5, 4, 4, 123)
            pass
            
        self.rot_cache = None  # invalidate cache
        return

    def _get_timer_str(self, now, alarm):
        missing_seconds = alarm.get_missing_time(now).seconds
        return ((alarm.message
                 if alarm.message
                 else "Timer") +
                " %02d:%02d" % (missing_seconds // 60, missing_seconds % 60))
    
    def add_alarm(self, now, alarm):
        print "Adding alarm"
        if alarm.type == Alarm.TYPE_TIMER:        
            rot = self.add_rotating_text(self._get_timer_str(now, alarm))
            self.running_alarms.append((alarm, rot))
            pass

    def remove_alarm(self, alarm):
        tmp = []
        for a in self.running_alarms:
            #print "REMOVING ALARM?? ", a[0].id, alarm.id, a[0].id == alarm.id
            if a[0].id == alarm.id:
                self.del_rotating_text(a[1])
            else:
                tmp.append(a)
                                
        self.running_alarms = tmp

    def start_alarm_mode(self, now, alarm):
        self.alarm_mode = True
        self.alarm_time = now

        if alarm.type == Alarm.TYPE_SCHEDULED:
            rot = self.add_rotating_text(alarm.message
                                         if alarm.message
                                         else alarm.name)
            self.running_alarms.append((alarm, rot))
            pass
        
        return

    def stop_alarm_mode(self, now, alarm, snoozed=None):
        self.alarm_mode = False
        self.alarm_time = 0

        if ((alarm.type == Alarm.TYPE_TIMER and not snoozed) or
            (alarm.type == Alarm.TYPE_SCHEDULED)):
            self.running_alarms = [(a, r)
                                   for a in self.running_alarms
                                   if a.id != alarm.id]
        return

    LONG_DEBUG_TEXT = "FARE LA LAVATRICE"

    last_pixels = None
    
    def rotate(self, strg, n):
        return strg[n:] + strg[:n]

    def loop(self, now):

        if (not self.last_rot or
            ((now - self.last_rot).microseconds > 500000)):
            if len(self.rotating) > 0:
                for a, rot in self.running_alarms:
                    if a.type == Alarm.TYPE_TIMER:
                        if a.playing:
                            self.set_rotating_text(rot, (a.message
                                                         if a.message
                                                         else a.name))
                        else:                            
                            self.set_rotating_text(rot, self._get_timer_str(now, a))

                if self.rot_cache:
                    string = self.rot_cache['string']
                    last_clear = self.rot_cache['next-clear']
                else:
                    self.rot_cache = {}
                    string = "   ".join(r[2] for r in self.rotating) + "     "
                    self.rot_cache['string'] = string
                    last_clear = None

                rotated = self.rotate(string, self.last_rot_idx)

                self.last_rot_idx = (self.last_rot_idx + 1) % len(string)

                self.lcd_area_clear(5, 4, 4, 123)

                chars = 5
                while chars < len(rotated):
                    w = self.get_font_width(rotated[:chars],
                                            fonts.tahoma.Tahoma22)
                    if w >= 118:
                        break
                    chars += 1
                    pass

                self.rot_cache['next-clear'] = self.text(5, 4,
                                                         rotated[:chars],
                                                         fonts.tahoma.Tahoma22)

                self.last_rot = now
            else:
                w = self.get_font_width(str("J"), fonts.wingdings.Wingdings)
                self.text((128 - w) // 2, 5, "J", fonts.wingdings.Wingdings)
        
        
        if self.alarm_mode and (now - self.alarm_time).microseconds >= 5000000:
            self.alarm_time = now
            self.toogle = not self.toggle
            pass

        if not self.last_update or ((now - self.last_update).microseconds >= 100000):
            #date_time = datetime.datetime.strftime(now, '%d %b %H:%M:%S')
            date_time = datetime.datetime.strftime(now, '%H:%M')
            date = datetime.datetime.strftime(now, '%S')

            if self.last_date is None or self.last_date != date:
                if AlarmDisplay.last_pixels > 0:
                    self.lcd_area_clear(105, 2, 2, AlarmDisplay.last_pixels)
                AlarmDisplay.last_pixels = self.text(105, 2, str(date),
                                                     fonts.tahoma.Tahoma12)
                self.last_date = date
            
            if self.last_time is None or self.last_time != date_time:
                self.lcd_area_clear(25, 0, 4, 80)
                w = self.get_font_width(str(date_time), fonts.tahoma.Tahoma26)
                self.text((128 - w) // 2, 0, str(date_time), fonts.tahoma.Tahoma26) 
                self.last_time = date_time


            self.last_update = now

        return


def json_respose_ok(data=None):
    res = { "status" : "ok" }

    if data is not None:
        res["data"] = data

    return res


def json_respose_error(message):
    return { "status" : "error", "message" : message }

def snooze(gpio_queue, path):
    gpio_queue.put(Message(Message.SNOOZE, data=1))
    return json_respose_ok()

def text_post(gpio_queue, path, data):
    gpio_queue.put(Message(Message.TEXT_168, data=(data['line'], data['text'])))
    return json_respose_ok()

def get_color(gpio_queue, gpio_json_pipe, path):
    gpio_json_pipe[0].send("color")
    color = gpio_json_pipe[0].recv()

    return json_respose_ok(data=color)

def post_color(gpio_queue, gpio_json_pipe, path, data):
    gpio_queue.put(Message(Message.COLOR, data=(data['R'],
                                                data['G'],
                                                data['B'])))
    return json_respose_ok()

def get_alarm_list(gpio_queue, gpio_json_pipe, path):
    gpio_json_pipe[0].send("alarm_list")
    _list = gpio_json_pipe[0].recv()

    return json_respose_ok(data=[a.to_json() for a in _list])

def post_alarm_list(gpio_queue, gpio_json_pipe, path, data):

    return json_respose_ok()

def del_alarm_list(gpio_queue, gpio_json_pipe, path):
    return json_respose_ok()

def json_server_process(gpio_queue, gpio_json_pipe):
    server = jserver.JSONServer("localhost", 8111)
    server.register_url("/snooze",
                        functools.partial(snooze, gpio_queue), None, None)
    server.register_url("/alarm",
                        functools.partial(get_alarm_list, gpio_queue, gpio_json_pipe),
                        functools.partial(post_alarm_list, gpio_queue, gpio_json_pipe),
                        functools.partial(del_alarm_list, gpio_queue, gpio_json_pipe),
    )
    server.register_url("/text",
                        None, functools.partial(text_post, gpio_queue), None)
    server.register_url("/color",
                        functools.partial(get_color, gpio_queue, gpio_json_pipe),
                        functools.partial(post_color, gpio_queue, gpio_json_pipe),
                        None)

    server.serve_forever()
    return

def update_google_events(front_display):
    now = datetime.datetime.now()

    front_display.lcd_area_clear(5, 0, 3, 15)
    front_display.text(5, 0, "q", fonts.webdings.Webdings14)
    try:
        evs = google.get_upcoming_events(now)

        existing_ids = set(a.tag for a in Alarm.ALARM_POOL)

        for e in evs:
            if e[0] not in existing_ids:
                Alarm.create_scheduled_alarm(e[1], name="Google sched " + e[2],
                                             message=e[2], tag=e[0])
        front_display.lcd_area_clear(5, 0, 3, 15)
        front_display.text(5, 0, "a", fonts.webdings.Webdings14)
    except:
        front_display.lcd_area_clear(5, 0, 3, 15)
        front_display.text(5, 0, "r", fonts.webdings.Webdings14)
        
    return


def gpio_process(gpio_queue, gpio_json_pipe):

    config = read_config()

    mixer = alsaaudio.Mixer(alsaaudio.mixers()[0])
    mixer.setvolume(config['volume'])

    # yeha, this is actually strange.. Didn't design it very well..
    write_config(config, Alarm.ALARM_POOL)

    if settings.ON_RASPBERRY:
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Setup the snooze button
        GPIO.setup(BUTTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        pass

    background = AlarmRGB(R, G, B)
    front_display = AlarmDisplay(LCD_CS, LCD_RST, LCD_A0, LCD_CLK, LCD_SI)
    snooze_button = button.Button(BUTTON)
    snooze_button.set_listener(SnoozeButtonListener(gpio_queue))
    
    front_display.text(3, 2, "ILUALARM", fonts.tahoma.Tahoma22)
    for x in xrange(5):
        front_display.lcd_area_clear(20, 5, 3, 104)
        front_display.text(20, 5, "Initializing.",
                           fonts.tahoma.Tahoma16)
        background.set_color(255, 0, 0)
        time.sleep(0.2)
        front_display.text(20, 5, "Initializing..", fonts.tahoma.Tahoma16)
        background.set_color(0, 255, 0)
        time.sleep(0.2)
        front_display.text(20, 5, "Initializing...", fonts.tahoma.Tahoma16)
        background.set_color(0, 0, 255)
        time.sleep(0.2)
    front_display.lcd_clear()

    now = datetime.datetime.now()
    
    red, green, blue = config['start-color']
    background.set_color(red, green, blue)
    
    active_alarm = None
    last_google_update = None
    
    if DEBUG and not Alarm.ALARM_POOL:
        a = Alarm.create_timer_alarm(now, 60,
                                     message="PASTIGLIA")

        front_display.add_alarm(now, a)
        
        write_config(config, Alarm.ALARM_POOL)

    while True:
        now = datetime.datetime.now()

        snooze_button.loop(now)
        background.loop(now)
        front_display.loop(now)
        Alarm.loop(now, config, background, front_display)

        try:
            message = gpio_queue.get_nowait()

            if message.type == Message.SNOOZE:
                active = Alarm.get_playing_alarms()
                if active:
                    snooze_for = (message.data or 1)
                    for a in active:
                        a.snooze(now, time=snooze_for)
                        front_display.stop_alarm_mode(now, a, snoozed=snooze_for)
                        
                    background.stop_alarm_mode(now)                        
                    if settings.ON_RASPBERRY:
                        stop_alarm_sound()
                pass
            elif message.type == Message.STOP:
                active = Alarm.get_playing_alarms()
                if active:
                    for a in active:
                        a.stop(now)
                        front_display.remove_alarm(a)
                        front_display.stop_alarm_mode(now, a)
                        
                    background.stop_alarm_mode(now)

                    if settings.ON_RASPBERRY:
                        stop_alarm_sound()
                pass
            elif message.type == Message.TEXT_168:
                front_display.small_text(2, message.data[0], message.data[1])
            elif message.type == Message.COLOR:
                red, green, blue = message.data
                background.set_color(red, green, blue)

            write_config(config, Alarm.ALARM_LOOP)
        except Exception:
            # No message to process..
            pass

        try:
            if gpio_json_pipe[1].poll():
                direct_message = gpio_json_pipe[1].recv()
                if direct_message == "alarm_list":
                    gpio_json_pipe[1].send(alarms)
                    pass
                elif direct_message == "color":
                    gpio_json_pipe[1].send({ 'R' : R, 'G' : G, 'B' : B})
                    pass
                elif direct_message == "quit":
                    GPIO.cleanup()
                    gpio_json_pipe[1].send("bye")
                    return  # quit
        except Exception:
            # No message to process..
            pass

        if last_google_update is None or (now - last_google_update).seconds >= 120:
            update_google_events(front_display)
            last_google_update = now
            pass
        
        time.sleep(0.02)
        pass # while True

    return

def kill_servers(gpio_server, json_server, gpio_json_pipe, signal, frame):
    # TODO: Does this work from a different process? NO!

    print "Killing.."
    if settings.ON_RASPBERRY:
        print "Sending signal.."
        gpio_json_pipe[0].send("quit")
        print "Waiting to process to finish.."
        done = gpio_json_pipe[0].recv()

    print "Terminating.."
    gpio_server.terminate()
    json_server.terminate()

    sys.exit(0)

if __name__ == "__main__":
    gpio_queue = multiprocessing.Queue()
    gpio_json_pipe = multiprocessing.Pipe()

    gpio_server = multiprocessing.Process(target=gpio_process,
                                          args=(gpio_queue, gpio_json_pipe))
    json_server = multiprocessing.Process(target=json_server_process,
                                          args=(gpio_queue, gpio_json_pipe))

    signal.signal(signal.SIGINT, functools.partial(kill_servers,
                                                   gpio_server,
                                                   gpio_queue,
                                                   gpio_json_pipe))

    gpio_server.start()
    json_server.start()

    gpio_server.join()
    json_server.join()

    GPIO.cleanup()
