from components.logger import Logger
import requests

class Spotify:
    def __init__(self, Database=None, Oauth=None, Watcher=None):
        self.dependencies = {"tier":"user", "dependencies":["Database", "Oauth", "Watcher"]}
        self.characteristics= ["timed"]
        self.capabilities = ["music", "spotify", "playback", "podcasts"]
        self.timing = {"unit": "seconds", "count":10}
        self.db = Database
        self.oauth = Oauth
        self.watcher = Watcher
        self.logger = Logger("Spotify").logger
        self.currentsong = ""
        # do not add init stuff

    def dostuff(self):
        data = {"playing": True, "Song":"Good thing", "Artist": "Zedd", "metadata":{"type":"update"}}
        msg = self.db.messagebuilder("Spotify", "update", data)
        self.watcher.publish(self, msg)


    def query(self, query, connectionID = 666):
        """connectionID is the id of who is asking(starts at 0, database is 999)
           the query is a dict containing the following keys:
            "category", "type", "data", "metadata"
            lets the system ask your module stuff.
        """
        category = query["category"]
        qtype = query["type"]
        qdata = query.get("data", None)
        metadata = query.get("metadata", None)
        response = {}
        # TODO: Read out the query
        # TODO: Use it to write out the response
        return response

    def getplaying(self):
        self.logger("getting token")
        ac = self.oauth.getaccesstoken()
        self.logger("Done")
        baseurl = "https://api.spotify.com/v1/me/player/currently-playing"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {ac}"
        }

        params = {'market': 'from_token'}

        self.logger("firing request")
        response = requests.get(baseurl, headers=headers, params=params)
        self.logger("Done")
        data = {}
        if len(response.content) > 1:
            playdata = response.json()
            item = playdata["item"]
            name = item["name"]
            self.logger(f"Currently playing: {name}")
            duration = item["duration_ms"]
            progress = playdata["progress_ms"]
            artists = [x["name"] for x in playdata["item"]["artists"]]
            playing = bool(playdata["is_playing"])
            #self.logger(playdata)
            if name != self.currentsong:
                self.currentsong = name
                data = {"playing":playing, "song": name, "artist": artists, "Progress":progress, "duration":duration}
                #self.logger(data)
            
            msg = self.db.messagebuilder("Spotify", "update", data)
            self.watcher.publish(self, msg)
        else:
            self.logger("nothing is playing")
            data = {"playing":False}
            msg = self.db.messagebuilder("Spotify", "update", data)
            self.watcher.publish(self, msg)
            self.logger("published")
        
    def startrun(self):
        """Various methods to control spotify playback"""
        # init stuff..
        self.logger = Logger("Spotify").logger
        self.logger("Startrun")
        self.datapath = f"data/modules/{self.__class__.__name__.lower()}"
        #self.dostuff()
        self.getplaying()
