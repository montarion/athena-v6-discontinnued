from components.logger import Logger
import re, datetime
class Killswitch:
    def __init__(self, Networking=None):
        self.dependencies = {"tier":"user", "dependencies":["Networking"]}
        self.capabilities = []
        self.timing = {"unit": "minutes", "count":10}
        self.shortest = 5 # shortest amount of inactivity before doing something
        self.rangedict = {str(list(range(5,9))): "one", str(list(range(9, 19))): "two", str(list(range(19, 25))): "three"}

    def readlogs(self):
        hostname = "GREYTITAN"
        search = f"(.*?) {hostname}(.*?)"
        with open('/var/log/auth.log') as logfile:
            for line in logfile:
                if "Accepted" in line:
                    result = re.search(search,line)
                    date = result.group(1)
                    lastlogin = datetime.datetime.strptime(date, '%b %d %H:%M:%S')
                    self.found = True
        if self.found:
            self.logger("last seen on: " + str(lastlogin)[5:])
            currentdate = datetime.datetime.strptime(datetime.datetime.now().strftime("%Y %B %d %H:%M:%S"),"%Y %B %d %H:%M:%S")
            delta = currentdate - lastlogin
            timesince = delta.seconds / 3600
            self.logger(f"time since last seen is: {timesince} hours.")
            state = self.getrange(timesince)
            if state:
                getattr(self, state)()
        else:
            self.logger("Didn't find succesfull login in today's log file, assuming 24 hours.", "debug")
            state = self.getrange(24)
            if state:
                getattr(self, state)()


    def getrange(self, timesince):
        t = int(float(timesince))
        for x in self.rangedict.keys():
            rangelist = eval(x)
            if t in rangelist:
                return self.rangedict[x]
        if t > self.shortest:
            self.logger(f"Didn't find time definitions for {t} hours, escalating.", "alert", "red")
            return self.rangedict[list(self.rangedict.keys())[-1]] # dicts are ordered since python3.6, so this works
        else:
            return False

    def one(self):
        self.logger("Running func one!")
        #TODO: ping last active device

    def two(self):
        self.logger("Running func two!")
        #TODO: ping all devices
    def three(self):
        self.logger("Running func three!")
        #TODO: send email to circle 1(Veerle, Daen, Nada) with last known location

    def four(self):
        #TODO: send email to circle 1 and 2 with location, call mum.
        pass
    def startrun(self):
        """Look through ssh logs for login info to determine user aliveness.
           If not alive, ping all devices x times, and then escalate to contacting humans."""
        #TODO: write some extra things to reset check-in time. e.g: active on phone(app is TBD), active on website
        # init stuff..
        self.found = False
        self.logger = Logger("Killswitch").logger
        self.datapath = f"data/modules/{self.__class__.__name__.lower()}"
        self.readlogs()
        
