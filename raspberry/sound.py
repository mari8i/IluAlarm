import subprocess

current_sound_process = None

def play_alarm_sound():
    global current_sound_process
    
    if current_sound_process is not None:
        print "PROCESS SOUND ALRESADY RUNNING..."
        return
        
    current_sound_process = \
        subprocess.Popen(["mplayer", "-loop", "0",
                          '/home/pi/ilualarm_devel/pikapi.wav'],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return
 
def stop_alarm_sound():
    global current_sound_process
    
    if current_sound_process is not None:
        current_sound_process.terminate()
        current_sound_process = None
    return


