from components.logger import Logger
import requests

class Spotify:
    def __init__(self, Database=None, Oauth=None):
        self.dependencies = {"tier":"user", "dependencies":["Database", "Oauth"]}
        self.characteristics= ["timed"]
        self.capabilities = ["music", "spotify", "playback", "podcasts"]
        self.timing = {"unit": "seconds", "count":10}
        self.db = Database
        self.oauth = Oauth
        self.logger = Logger("Spotify").logger
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
        ac = self.oauth.getaccesstoken()
        baseurl = "https://api.spotify.com/v1/me/player/currently-playing"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {ac}"
        }

        params = {'market': 'from_token'}

        response = requests.get(baseurl, headers=headers, params=params)
        data = {}
        if len(response.content) > 1:
            self.logger(response.json(), "debug")
            playdata = response.json()
            item = playdata["item"]
            name = item["name"]
            duration = item["duration_ms"]
            progress = playdata["progress_ms"]
        else:
            self.logger("nothing is playing")
        
    def startrun(self):
        """Various methods to control spotify playback"""
        # init stuff..
        self.logger = Logger("Spotify").logger
        self.datapath = f"data/modules/{self.__class__.__name__.lower()}"
        self.watcher = self.db.membase["classes"]["Watcher"]
        self.dostuff()
        data = {"foo":"bar"}
