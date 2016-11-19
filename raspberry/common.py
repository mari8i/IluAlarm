import rgb
import json
import datetime
import multiprocessing

class Message(object):

    SNOOZE = 0
    TEXT_168 = 1
    COLOR = 2
    STOP = 3
    VOLUME = 4

    def __init__(self, _type, data=None):
        self.type = _type
        self.data = data
        return

    pass

class Communication(object):
    
    def __init__(self):
        self.gpio_queue = multiprocessing.Queue()
        self.gpio_json_pipe = multiprocessing.Pipe()
        return

    def cmd_to_gpio(self, cmd, data=None):
        self.gpio_json_pipe[0].send((cmd, data))
        return self.gpio_json_pipe[0].recv()
    
    def pop_gpio_cmd(self):
        if self.gpio_json_pipe[1].poll():
            return self.gpio_json_pipe[1].recv()
        return None

    def gpio_reply(self, reply):
        self.gpio_json_pipe[1].send(reply)
        return

    def msg_to_gpio(self, type, data=None):
        self.gpio_queue.put(Message(type, data=data))

    def pop_gpio_msg(self):
        try:
            return self.gpio_queue.get_nowait()
        except Exception:
            return None

    def pop_gpio_cmd_exec(self, now, exec_map, arg):
        tmp = self.pop_gpio_cmd()
        if tmp is not None:
            cmd, data = tmp
            try:
                self.gpio_reply(exec_map[cmd](now, data, arg))
            except Exception as e:
                print e
                self.gpio_reply(None)
                
        return

    def pop_gpio_msg_exec(self, now, exec_map, arg):
        msg = self.pop_gpio_msg()    
        if msg is not None:
            try:
                exec_map[msg.type](now, msg.data, arg)
            except Exception as e:
                print e
        return

        
    pass
    

class Alarm(object):
    
    TYPE_SCHEDULED = 0
    TYPE_TIMER = 1

    # Type of alarms
    # 1. once at a certain date
    # 2. starting from a date, every N hours repeated.
    # 3. Timer

    # TODO Ideas:
    # Alarm that when snoozed goes to the next message
    # Example usage: when doing a receip that has a sequence of timings
    
    def __init__(self, id, type, time, name=None,
                 message=None, enabled=True, tag=None):
        self.id = id

        self.tag = tag
        self.type = type
        self.name = name
        if not self.name:
            self.name = "ALARM " + str(self.id)

        self.set_time = time
        self.time = time
        self.snoozed = False
        self.message = message
        self.enabled = enabled
        self.playing = None
        return

    def is_timer(self):
        return self.type == Alarm.TYPE_TIMER

    def is_scheduled(self):
        return self.type == Alarm.TYPE_SCHEDULED

    def is_playing(self):
        return self.playing is not None

    def is_snoozed(self):
        return self.snoozed
    
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

    def get_missing_time(self, now):
        return self.time - now
    
    def snooze(self, now, time=10):
        """
        time is in minutes
        """

        self.time = now + datetime.timedelta(minutes=time)
        self.snoozed = True
        self.playing = None
        return

    def stop(self, now):
        print "Stopping alarm"

        if self.is_scheduled() and self.repeat_every is not None:
            self.time += datetime.timedelta(minutes=self.repeat_every)
            self.set_time = self.time
            self.playing = None
            return True
        else:
            self.time = None

            # No repeat, no snooze.. Disable this alarm. 
            self.enabled = False
            
        self.playing = None

        return False

    def is_snooze_timeout(self, now, timeout=10):
        """in minutes"""
        return self.playing is not None \
            and (now - self.playing).seconds >= (timeout * 60)
    
    def should_play(self, now):
        # Alarm not enabled.. well.. skip
        if not self.enabled:
            return False

        # Start time is set and time has passed..
        if self.time and self.time < now:
            return True

        return False

    def play(self, now):
        self.playing = now
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
            "tag" : self.tag,
        }

        if self.type == Alarm.TYPE_SCHEDULED:
            res['repeat_every'] = self.repeat_every
        elif self.type == Alarm.TYPE_TIMER:
            res['timeout'] = self.timeout

        return res

    def __str__(self):
        return self.message if self.message else self.name

    pass


class Config(object):

    CONFIG_VERSION = 4
    CONFIG_FILE = "/home/pi/ilualarm.conf"
    
    def __init__(self):
        self.requires_save = False
        
        self.defaults = {
            "version" : Config.CONFIG_VERSION,
            "alarms" : [],
            "color" : rgb.ILARIA, # (R, G, B)
            "volume" : 80, # 0..100
            "snooze_timeout" : 5, # ?
            "snooze" : 10,        # minutes
            "text" : "IluAlarm",
        }

        self.settings = self.defaults.copy()
        
        try:
            with open(Config.CONFIG_FILE, "r") as fc:
                saved = json.load(fc)

                if not saved['version'] or saved['version'] < Config.CONFIG_VERSION:
                    self.save()
                else:
                    self.settings.update(saved)
                pass
        except Exception as e:
            print e
            self.save()
            pass

        self.settings['alarms'] = [Alarm.from_json(pa)
                                   for pa in self.defaults['alarms']]

        self.curr_alarm_id = 0
        
        if self.settings['alarms']:
            self.curr_alarm_id = max(a.id for a in self.settings['alarms']) 
        return

    def get(self, key):
        return self.settings[key]

    def set(self, key, value):
        self.settings[key] = value
        self.notify_update()
    
    def get_volume(self):
        return self.settings['volume']

    def set_volume(self, volume):
        self.settings['volume'] = volume
        self.notify_update()

    def get_color(self):
        return self.settings['color']

    def set_color(self, color):
        self.settings['color'] = color
        self.notify_update()
    
    def get_alarms(self):
        return self.settings['alarms']
    
    def get_enabled_alarms(self):
        return (a for a in self.settings['alarms'] if a.enabled)

    def remove_alarm(self, alarm_id):
        self.settings['alarms'] = [a
                                   for a in self.settings['alarms']
                                   if a.id != alarm_id]
        self.notify_update()
        return

    def has_playing_alarms(self):
        return any((a.playing 
                    for a in self.settings['alarms']))
    
    def get_playing_alarms(self):
        return set((a
                    for a in self.settings['alarms']
                    if a.playing is not None))

    def get_timer_alarms(self, playing=None):
        return set((a
                    for a in self.settings['alarms']
                    if a.is_timer() and (playing is None or
                                         a.is_playing() == playing)))

    def get_scheduled_alarms(self):
        return set((a
                    for a in self.settings['alarms']
                    if a.is_scheduled()))
    
    def create_scheduled_alarm(self, start_time, name=None,
                               message=None, repeat_every=None,
                               tag=None):
        """
        repeat_every is in minutes
        """

        self.curr_alarm_id += 1
        
        a = Alarm(self.curr_alarm_id,
                  Alarm.TYPE_SCHEDULED, start_time,
                  name=name, message=message, tag=tag)

        a.repeat_every = repeat_every

        self.settings['alarms'].append(a)
        self.notify_update()        
        return a

    def create_timer_alarm(self, now, timeout, name=None,
                           message=None, tag=None):
        """
        timeout is in seconds
        """
        
        self.curr_alarm_id += 1
        
        a = Alarm(self.curr_alarm_id, Alarm.TYPE_TIMER,
                  now + datetime.timedelta(seconds=timeout),
                  name=name, message=message, tag=tag)

        a.timeout = timeout
        
        self.settings['alarms'].append(a)

        self.notify_update()
        return a

    def find_alarm(self, id):
        for a in self.settings['alarms']:
            if a.id == id:
                return a
        return None
            
    def notify_update(self):
        self.requires_save = True
        return
    
    def save(self, force=False):
        if not force and not self.requires_save:
            return
        
        dump = self.settings.copy()

        dump['alarms'] = [a.to_json()
                          for a in self.settings['alarms']]

        with open(Config.CONFIG_FILE, "w") as fc:
            json.dump(dump, fc)
            pass

        self.requires_save = False
        return
    
    pass
