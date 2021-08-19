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

    def oldgetauthorized(self):
        # let user login
        baseurl = "https://accounts.spotify.com/authorize"
        scopes = ["user-read-currently-playing", "user-modify-playback-state", "user-library-modify"]
        client_id = self.db.query(["spotify", "client_id"], "credentials")["resource"]
        params= {
                "client_id":client_id, # TODO: guide the user to get their own
                "response_type": "code",
                #"redirect_uri": "https://github.com/montarion/athena",
                "scope": ' '.join(scopes)
                }
        #r = requests.get(baseurl, params=params)
        auth_code = self.oauth.getauthorized(baseurl, params)
        return auth_code
        #loginurl = r.url
        #self.logger(loginurl)
        
        # Figure out how you want to do setup stuff. (just use the desktop client for now!)
        # write an OAUTH support class(nonspecific, so it works with all oauth stuff)


    def authorize(self):
        # STUB, get this from the getauthorized() method
        token = self.db.query(["spotify", "auth_token"], "credentials")
        return {"token": token, "success": True}

    def oldgetaccess(self):
        # check if accesstoken
        
        baseurl = "https://accounts.spotify.com/api/token"
        
        # if not accesstoken
        auth_code = self.getauthorized()
        #auth_code = "AQCyFSpjHrniBnyQBHwng-2gDUMVKNYhKm3jKTW6pQ63HBQ9sJrrExIZ3AS-mkoXmw4SGYn2Wc3WB_oPFIkZXVU7sXIQvNeKOMILrBIqen4lpTti8__sB9qSbaSiM_z-EN9_TPnNe0u1fScm5hex9YlCIcsCZqQVs8KSoZsHqaMdwjRopqfi27Y1OTQmDcZqUumoKhX-ENVaa3GpFhpVyTN2HNnq_vwFWmCbH0Nx-j7GNTA29zKQwDcPuMmammnPodnJ6FNW7cGDEHpv1t3mQ5gtl9y8"
        client_id = self.db.query(["spotify", "client_id"], "credentials")["resource"]
        client_secret = self.db.query(["spotify", "client_secret"], "credentials")["resource"]
        return self.oauth.getaccesstoken(baseurl, auth_code, client_id, client_secret)

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
