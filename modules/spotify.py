from components.logger import Logger
import requests

class Spotify:
    def __init__(self, Database=None):
        self.dependencies = {"tier":"user", "dependencies":["Database"]}
        self.characteristics= ["timed"]
        self.capabilities = ["music", "spotify", "playback", "podcasts"]
        self.timing = {"unit": "seconds", "count":10}
        self.db = Database
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

    def getauthorized(self):
        # let user login
        baseurl = "https://accounts.spotify.com/authorize"
        scopes = ["user-read-currently-playing", "user-modify-playback-state", "user-library-modify"]
        params= {
                "client_id": self.db.query(["spotify", "client_id"], "credentials"), # TODO: guide the user to get their own
                "response_type": "code",
                "redirect_uri": "https://github.com/montarion/athena",
                "scope": ' '.join(scopes)
                }
        r = requests.get(basurl, params=params)
        loginurl = r.url
        # Figure out how you want to do setup stuff. (just use the desktop client for now!)
        # write an OAUTH support class(nonspecific, so it works with all oauth stuff)


    def authorize(self):
        # STUB, get this from the getauthorized() method
        token = self.db.query(["spotify", "auth_token"], "credentials")
        return {"token": token, "success": True}

    def getplaying(self):
        baseurl = "https://api.spotify.com/v1/me/player/currently-playing"
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.authorize()['token']}"
        }

        params = {'market': 'from_token'}

        response = requests.get(baseurl, headers=headers, params=params)
        self.logger(response, "debug")                
        self.logger(response.json(), "debug")
        
    def startrun(self):
        """Various methods to control spotify playback"""
        # init stuff..
        self.logger = Logger("Spotify").logger
        self.datapath = f"data/modules/{self.__class__.__name__.lower()}"
        self.watcher = self.db.membase["classes"]["Watcher"]
        self.dostuff()
        data = {"foo":"bar"}
