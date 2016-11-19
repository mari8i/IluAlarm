import multiprocessing
import sys
import signal
import functools



# IluAlarm imports
import settings
import gpio
import server
import common

def kill_servers(gpio_server, com, signal, frame):
    # TODO: Does this work from a different process? NO!

    print "Killing.."
    res = com.cmd_to_gpio("quit")
    print res

    print "Terminating.."
    gpio_server.terminate()

    sys.exit(0)

if __name__ == "__main__":
    com = common.Communication()

    gpio_server = multiprocessing.Process(target=gpio.gpio_process,
                                          args=(com, ))

    signal.signal(signal.SIGINT, functools.partial(kill_servers,
                                                   gpio_server,
                                                   com))
    gpio_server.start()
    
    server.json_server_process(com)

    gpio_server.join()
