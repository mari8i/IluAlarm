import settings
import ConfigParser
import subprocess
import time

class MopidySpotify(object):

    def __init__(self, config_file=settings.MOPIDY_CONF):
        self.path = config_file
        self.cfg = ConfigParser.ConfigParser()
        self.cfg.read(self.path)
        return

    def set_credentials(self, username, password):
        self.cfg.set('spotify', 'enabled', "true")
        self.cfg.set('spotify', 'username', username)
        self.cfg.set('spotify', 'password', password)
        return

    def get_credentials(self):
        return (self.cfg.get('spotify', 'username'),
                self.cfg.get('spotify', 'password'))

    def save(self):
        with open(self.path, "w") as cfg_f:
            self.cfg.write(cfg_f)

    @staticmethod
    def run_mopidy():
        subprocess.call(["pkill", "-kill", "mopidy"])
        #print os.spawnl(os.P_NOWAIT, " ".join(["/usr/bin/mopidy", "--config", settings.MOPIDY_CONF]))
        pid = subprocess.Popen(["/usr/bin/mopidy", "--config", settings.MOPIDY_CONF], shell=True).pid
        print pid

        #time.sleep(20)
        return

    pass

#MopidySpotify.run_mopidy()
