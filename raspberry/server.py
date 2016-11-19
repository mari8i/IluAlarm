
# IluAlarm imports
import json_server as jserver
from common import Message
import spotify

def json_respose_ok(data=None):
    res = { "status" : "ok" }

    if data is not None:
        res["data"] = data

    return res

def json_respose_error(message):
    return { "status" : "error", "message" : message }

def snooze(path, match, com):
    com.msg_to_gpio(Message.SNOOZE, data=10)
    return json_respose_ok()

def stop(path, match, com):
    com.msg_to_gpio(Message.STOP, data=10)
    return json_respose_ok()

def text_post(path, match, data, com):
    com.msg_to_gpio(Message.TEXT_168, data=data['text'])
    return json_respose_ok()

def text_get(path, match, com):
    text = com.cmd_to_gpio("text")
    return json_respose_ok(data={'text': text})

def volume_post(path, match, data, com):
    com.msg_to_gpio(Message.VOLUME, data=data['volume'])
    return json_respose_ok()

def volume_get(path, match, com):
    volume = com.cmd_to_gpio("volume")
    return json_respose_ok(data={'volume': volume})

def get_color(path, match, com):
    color = com.cmd_to_gpio("color")
    return json_respose_ok(data=color)

def post_color(path, match, data, com):
    com.msg_to_gpio(Message.COLOR, data=(data['r'],
                                         data['g'],
                                         data['b']))
    return json_respose_ok()

def get_spotify_conf(path, match, com):
    spot_conf = spotify.MopidySpotify()
    cred = spot_conf.get_credentials()
    return json_respose_ok(data=cred)

def post_spotify_conf(path, match, data, com):
    spot_conf = spotify.MopidySpotify()
    spot_conf.set_credentials(data['username'],
                              data['password'])
    spot_conf.run_mopidy()
    return json_respose_ok()

def get_alarm_list(path, match, com):
    _list = com.cmd_to_gpio("alarm_list")
    print "ALARMS:", _list
    return json_respose_ok(data=_list)

def post_alarm_list(path, match, data, com):
    if data['id'] >= 1:
        alarm = com.cmd_to_gpio("edit_alarm", data)
    else:
        alarm = com.cmd_to_gpio("create_alarm", data)
        
    if alarm is not None:
        res = json_respose_ok(data=alarm)
        return res
    else:
        return json_respose_error("Unable to add/edit alarm")

def del_alarm_list(path, match, com):
    return json_respose_ok()

def json_server_process(com):

    server = jserver.JSONServer("0.0.0.0", 8111, bundle=com)

    server.register_url("^/snooze/$", get=snooze)

    server.register_url("^/stop/$", get=stop)

    server.register_url("^/alarm/$",
                        get=get_alarm_list,
                        post=post_alarm_list,
                        delete=del_alarm_list)

    server.register_url("^/text/$",
                        get=text_get,
                        post=text_post)

    server.register_url("^/volume/$",
                        get=volume_get,
                        post=volume_post)

    server.register_url("^/color/$",
                        get=get_color,
                        post=post_color)

    server.register_url("^/spotify/$",
                        get=get_spotify_conf,
                        post=post_spotify_conf)

    server.serve_forever()
    return
