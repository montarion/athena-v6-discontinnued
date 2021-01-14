from components.logger import Logger

import requests, re, os, json, traceback, time
class Weather:
    def __init__(self, Database=None, Watcher=None):
        self.dependencies = {"tier":"standalone", "dependencies":["Database", "Watcher"]}
        self.capabilities = ["timed", "async"]
        self.timing = {"unit": "minutes", "count":10}
        self.datapath = f"data/modules/{self.__class__.__name__.lower()}"
        self.db = Database
        self.watcher = Watcher
        self.logger = Logger("Weather").logger
        self.iconbase = "http://openweathermap.org/img/wn/"
        # do not add init stuff


    def websetuptest(self): # here as a test
        # make request for info through whatever is registered as main(/current?) ui
        # wait for the answer without blocking the main thread
        # but pause the execution of the current program(through db query?)
        #asker = self.__class__.__name__
        questionlist = [{"type": "text", "question": "Where do you live?"}]
        
        self.logger("RELOAD PAGE NOW", "alert", "red")
        time.sleep(5)
        t = self.db.getfromuser(questionlist)
        self.logger(f"GOT USER RESULTS! - {t}", "info", "green")

    def getcurrentweather(self):
        if not self.watcher:
            self.watcher = self.db.membase["classes"]["Watcher"]
        self.location = self.db.query("city", "personalia")["resource"]
        apikey = self.db.query(["weather", "apikey"], "credentials")
        if str(apikey["status"])[:2] == "20":
            apikey = apikey["resource"]
        else:
            self.logger("Couldn't find apikey, or user didn't respond. Exiting.")
            exit() # TODO: only kill this job, and provide feedback through the ui
        coords = self.db.query("coordinates", "personalia") #"40.677748", "-73.906903"
        if coords["status"][:2] == "20": # check if success
            lat,lon = coords["resource"]
        else:
            self.logger("Couldn't find coordinates, or user didn't respond. Exiting.")
            exit() # TODO: only kill this job, and provide feedback through the ui
        baseurl = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely&appid={apikey}&units=metric"

        #TODO try-catch this HTTP request
        res = requests.get(baseurl).json()
        if len(res.keys()) == 2:
            # error occured, read message
            self.logger(f"Error: {res['cod']}", "alert", "red")
            self.logger(f"Message: {res['message']}", "alert", "red")

        try:
            timezone = res["timezone"]
            # maybe write to file
            weatherdict = {}

            # current weather
            curdict = self.parsecurrent(res["current"])
            self.db.write("currentweather", curdict, "weather")
            weatherdict["current"] = curdict

            # next x(3) hours
            hourdict = self.parsehourly(res["hourly"], 3)
            self.db.write("hourforecast", hourdict, "weather")
            weatherdict["hours"] = hourdict

            # tomorrow
            tomorrowdict = self.parsetomorrow(res["daily"])
            self.db.write("tomorrowforecast", tomorrowdict, "weather")
            weatherdict["tomorrow"] = tomorrowdict

            # publish it
            self.watcher.publish(self, weatherdict)
            return {"status":200, "resource":weatherdict}
        except Exception as e:
            self.logger(e, "alert", "red")
            traceback.print_exc()
            return {"status":503, "resource": "something went wrong."}

    def parsecurrent(self, data):
        pdict = {
            "location": self.location,
            "dt": data["dt"],
            "temp": data["temp"],
            "feelslike": data["feels_like"],
            "sunrise": data["sunrise"],
            "sunset": data["sunset"],
            "clouds": data["clouds"],
            "windspeed": data["wind_speed"],
            "iconurl": self.iconbase + data["weather"][0]["icon"] + "@2x.png"
                }
        if "rain" in data:
            pdict["rain"] = data["rain"]
        # uitest
        pdict["background"] = "https://i.imgur.com/oOz9jCd.gif"
        return pdict

    def parsehourly(self, data, hours):
        tmplist = []
        for d in data[1:hours+1]:
            tmpdict = {
                "location": self.location,
                "dt": d["dt"],
                "temp": d["temp"],
                "feelslike": d["feels_like"],
                "clouds": d["clouds"],
                "windspeed": d["wind_speed"],
                "pop": d["pop"],
                "iconurl": self.iconbase + d["weather"][0]["icon"] + "@2x.png"
            }
            tmplist.append(tmpdict)
        return tmplist
    def parsetomorrow(self, data):
        data = data[0] # only pick tomorrow
        tdict = {
            "location": self.location,
            "dt": data["dt"],
            "temp": data["temp"],
            "feelslike": data["feels_like"],
            "sunrise": data["sunrise"],
            "sunset": data["sunset"],
            "clouds": data["clouds"],
            "windspeed": data["wind_speed"],
            "iconurl": self.iconbase + data["weather"][0]["icon"] + "@2x.png"
        }
        return tdict
    def startrun(self):
        """this is what gets called by main"""
        # init stuff..
        self.logger("running weather")
        #self.websetuptest()
        return self.getcurrentweather()
        
