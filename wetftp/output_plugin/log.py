import os
import time
from wetftp import config

# path of log files
logpath = config.cfg.get("log", "path")
if not os.path.exists(logpath):
    os.makedirs(logpath)

# sensor name
name = config.cfg.get("wetftp", "name")


class plugin(object):
    def __init__(self, hacker_ip):
        self.hacker_ip = hacker_ip
        self.logpath = None
        self.get_logpath()

    def get_logpath(self):
        self.logpath = os.path.join(logpath, self.hacker_ip)
        if not os.path.exists(self.logpath):
            os.makedirs(self.logpath)

    def send(self, subject, action, content):
        if action == 'cmd':
            with open(os.path.join(self.logpath, 'cmd.log'), 'a') as logfile:
                log = ' '.join([time.strftime("%y%m%d-%H:%M:%S"), content, '\n'])
                logfile.write(log)
        elif action == 'file':
            with open(os.path.join(self.logpath, str(time.time())), 'ab') as logfile:
                logfile.write(content)
