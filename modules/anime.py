import os, requests, json, feedparser, re, time
from time import sleep
from components.logger import Logger

class Anime:
    def __init__(self, Networking=None, Watcher=None, Database=None):
        self.dependencies = {"tier": "user", "dependencies":["Networking", "Watcher", "Database"]}
        self.capabilities = ["timed"]
        self.timing = {"unit": "minutes", "count":2}
        self.networking = Networking
        # geen basics
        self.watcher = Watcher
        self.dbobj = Database
        self.datapath = f"data/modules/{self.__class__.__name__.lower()}"
        self.retval = None
        # other init stuff happens in startrun

    def getshows(self, number = 1):
        base = f"https://nyaa.si/?page=rss&q={self.publishchoice}+%2B+(1080p)&c=1_2&f=2"
        feed = feedparser.parse(base)
        entries = feed.entries
        sessiondict = {}
        x = 0
        while x < number and x <= len(entries):
            try:
                entry = entries[x]
            except IndexError:
                self.logger(f"Tried index {x} and failed.") 
                x+=1
            if "[v0]" in entry["title"]:
                break # don't want the weird v0 stuff from erai raws.
            try:
                title, show, episode = self.cleantitle(entry["title"])
            except:
                x +=1
                number += 1
                continue
            link = entry["link"]
            if self.checkshow(show):
                self.logger(f"current: {show} episode {episode}")
                sessiondict["title"] = show
                sessiondict["episode"] = episode
                if show not in self.maindict:
                    imagelink, bannerlink, maxepisodes = self.getinfo(show) #TODO add synopsis
                    self.maindict[show] = {"art":{}, "meta":{}}
                    self.maindict[show]["art"]["cover"] = imagelink
                    self.maindict[show]["art"]["banner"] = bannerlink
                    self.maindict[show]["meta"]["maxepisodes"] = maxepisodes
                sessiondict["art"] = {}
                sessiondict["art"]["cover"] = self.maindict[show]["art"]["cover"]
                sessiondict["art"]["banner"] = self.maindict[show]["art"]["banner"]

                self.maindict[show]["lastep"] = episode
                animedict = self.dbobj.gettable("anime")["resource"]
                lastshow = self.dbobj.query(["lastshow", "title"], "anime")["resource"]
                #if animedict.get("lastshow", {"title":"show"})["title"] != show:
                if lastshow != show:
                    self.download(show, link)
                    ct = int(time.time())
                    self.maindict[show]["aired_at"] = ct
                    sessiondict["aired_at"] = ct
                    #targetlist = settings().checkavailability("computing")["resource"]
                    #if len(targetlist) == 0:
                    #Event().anime("aired")

                    # send the message - Just publish this and let someone else take care of it. example: "{type: "new show"} in metadata, for whoever is listening
                    #idlist = self.networking.findtarget("greytest")
                    #self.logger(f"REMOVE HARDCODED TARGET", "alert", "yellow")
                    category = "anime"
                    type = "latest"
                    artdict = sessiondict["art"]
                    data = {"category": "anime", "type": "update", "data": {"title":show, "lastep": episode, "art":artdict, "aired_at":ct}}
                    self.retval = data
                    metadata = {"status": 200}
                    #res = self.networking.messagebuilder(category, type, data, metadata, "all")
                    self.dbobj.write("lastshow", sessiondict, "anime")


                x += 1
            else:
                number += 1
                x += 1
        self.dbobj.write("maindict", self.maindict, "anime")
        if self.retval:
            tmp = {"status": 200, "resource": self.retval, "successful":True}
            self.retval = None
            return tmp


    def checkshow(self, show):
        # lets you check for substrings of shows as well. e.g. "One" will match "One Piece".
        try:
            res = [s for s in self.watchlist if show in s]
        except:
            res = ""
        if len(res) > 0:
            return True
        else:
            return False

    def cleantitle(self, title):
        pattern = "\[.*\] (.*) - ([0-9]*) .*\[|\(1080p\]|\).*.mkv"
        try:
            res = re.search(pattern, title)
            show = res.group(1)
            episode = res.group(2)
            newtitle = f"{show} - {episode}.mkv"
            return newtitle, show, episode
        except:
            self.logger(f"Failure to parse title: {title}", "alert", "red")
            return None

    def getinfo(self, name):
        query = "query($title: String){Media (search: $title, type: ANIME){episodes, bannerImage, coverImage{extraLarge}}}" # this is graphQL, not REST
        variables = {'title': name}
        url = 'https://graphql.anilist.co'
        response = requests.post(url, json={'query': query, 'variables': variables})
        self.logger(response)
        preurl = json.loads(response.text)["data"]["Media"]

        coverdict = preurl["coverImage"]
        bannerurl = preurl["bannerImage"]
        maxepisodes = preurl["episodes"]

        coverurl = coverdict[list(coverdict.keys())[0]]
        if bannerurl == None:
            bannerurl = coverurl

        return coverurl, bannerurl, maxepisodes

    def download(self, show, link):
        # check if folder exists:
        root = "/mnt/raspidisk/files/anime/"
        truepath = os.path.join(root, "\ ".join(show.split(" ")))
        check = os.path.isdir(truepath)
        if not check:
            self.logger("creating folder for {}".format(show), "debug")
            precommand = "sudo -H -u pi bash -c \""
            command = "mkdir {}".format(truepath)
            postcommand = "\""
            os.system(precommand + command + postcommand)
        else:
            self.logger("folder {} already existed".format(show), "debug")
        precommand = "sudo -H -u pi bash -c \""
        command = (precommand + r"deluge-console 'add -p {} {}'".format(truepath, link) + "\"")
        os.system(command)

    def findshows(self):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from bs4 import BeautifulSoup

        url = "https://www.subsplease.org/schedule/"
        chrome_opts = Options()
        chrome_opts.add_argument("--headless")
        chrome_opts.add_argument("--disable-gpu")
        chrome_opts.add_argument("--disable-extensions")
        chrome_opts.add_argument("--log-level=OFF")
        chrome_opts.add_argument("--disable-dev-shm-usage")
        chrome_opts.add_argument("--no-sandbox")
        driver = webdriver.Chrome(options=chrome_opts)
        driver.get(url)
        sleep(6)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        preshows = soup.find_all("td", {"class":"all-schedule-show"})
        showlist = []
        chosenlist = []
        for show in preshows:
            showlist.append(''.join(show.text))

        for i, show in enumerate(showlist):
            print("Show number {} is: {}".format(i + 1, show))
            interest = input("w to add {}".format(show))
            if interest == "w":
                chosenlist.append(show)
        result = self.dbobj.write("watchlist", chosenlist, "anime")

        return chosenlist

    def query(self, query, connectionID=666):
        """connectionID is the id of who is asking(starts at 0, database is 999)
           the query is a dict containing the following keys:
            "category", "type", "data", "metadata"
        """
        category = query["category"]
        qtype = query["type"]
        qdata = query.get("data", None)
        metadata = query.get("metadata", None)
        response = {}
        if category == "request":
            if qtype == "lastshow":
                lastshow = self.dbobj.query(["lastshow"], "anime")["resource"]
                response = {"category":"anime", "type":"lastshow", "data":lastshow}

            if qtype == "eplist":
                title = qdata["title"]
                # get base from db
                showfolder = f"/mnt/raspidisk/files/anime/{title}"
                # if folder exists:
                prelist = sorted(os.listdir(showfolder))
                findict = {}

                _, show, episode = self.cleantitle(prelist[0])
                for file in prelist:
                    _, _, episode = self.cleantitle(file)
                    size = os.stat(os.path.join(showfolder, file)).st_size/1000000 # was bytes, now MB
                    unit = "MB"
                    if size > 1000:
                        unit = "GB"
                        size = size/1000
                    size = f"{size:,.2f}"
                    compressed = False
                    if "compressed" in file:
                        compressed = True
                    findict[episode] = {"size": size, "unit":unit, "compressed": compressed}
                response = {"category": "anime", "type":"eplist", "data":findict}
        # TODO: Read out the query
        # TODO: Use it to write out the response
        return response

    def catchup(self, showname):
        base = f"https://nyaa.si/?page=rss&q={self.publishchoice}+%2B+(1080p)+{showname.replace(' ','%20')}&c=1_2&f=2"
        feed = feedparser.parse(base)
        entries = feed.entries
        entries.reverse()
        sessiondict = {}
        number = 75 #nyaa.si max
        x = 0
        while x < number and x <= len(entries):
            try:
                entry = entries[x]
            except IndexError:
                self.logger(f"Tried index {x} and failed.")
                x+=1
                continue
            if "[v0]" in entry["title"]:
                break # don't want the weird v0 stuff from erai raws.
            try:
                title, show, episode = self.cleantitle(entry["title"])
            except:
                x +=1
                number += 1
                continue
            link = entry["link"]
            if show == showname:
                self.logger(f"current: {show} episode {episode}")
                sessiondict["title"] = show
                sessiondict["episode"] = episode
                if show not in self.maindict:
                    imagelink, bannerlink, maxepisodes = self.getinfo(show) #TODO add synopsis
                    self.maindict[show] = {"art":{}, "meta":{}}
                    self.maindict[show]["art"]["cover"] = imagelink
                    self.maindict[show]["art"]["banner"] = bannerlink
                    self.maindict[show]["meta"]["maxepisodes"] = maxepisodes
                sessiondict["art"] = {}
                sessiondict["art"]["cover"] = self.maindict[show]["art"]["cover"]
                sessiondict["art"]["banner"] = self.maindict[show]["art"]["banner"]

                self.maindict[show]["lastep"] = episode
                animedict = self.dbobj.gettable("anime")["resource"]
                lastshow = self.dbobj.query(["lastshow", "title"], "anime")["resource"]
                #if animedict.get("lastshow", {"title":"show"})["title"] != show:
                self.download(show, link)
                ct = int(time.time())
                self.maindict[show]["aired_at"] = ct
                sessiondict["aired_at"] = ct
                self.dbobj.write("lastshow", sessiondict, "anime")

                x += 1
            else:
                number += 1
                x += 1
        self.dbobj.write("maindict", self.maindict, "anime")
        result ={"status": 200}
        return result

    def startrun(self, number = 1):
        self.logger = Logger("Anime").logger
        # add actual class to membase
        #self.dbobj.membase["classes"][_
        self.publishchoice = "SubsPlease"
        prelist = self.dbobj.query("watchlist", "anime")
        if prelist["status"][:2] == "20":
            self.watchlist = prelist["resource"]
            
        else:
            self.watchlist = self.findshows()

        predict = self.dbobj.query("maindict", "anime")
        if predict["status"][:2] == "20":
            self.maindict = predict["resource"]
        else:
            self.maindict = {}

        result = self.getshows(number)
        
        if result and "status" in result and result["status"] == 200:
            return result
