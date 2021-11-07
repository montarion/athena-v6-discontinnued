#use the pubsub scheme in watcher.py to catch the websocket message with the code from the website,
#and continue the flow after

#1. get authorization from user(you give them an url, you register a subscription to OAUTH, they log in, they get redirected to your site, you get the code from the url and send it back to the server under category OAUTH, the server published the OAUTH message, and you continue.)
#2. get a token from the service(exchange the code for an auth token and a refresh token. save these, and return the accesstoken to whoever asked
#3. have an "authorize" method, that receives a url and parameters. in the method, add the OAUTH compliant header(with the auth token), and return the result to whoever asked. if necessary, use the refresh token to get a new token.


from components.logger import Logger
import requests, time

class Oauth:
    def __init__(self,Database=None):
        self.logger = Logger("Oauth").logger
        self.db = Database
        self.watcher_loaded = False

        self.res = None

    def getauthorized(self, caller):
        # let user login
        auth_url = self.db.query([caller, "auth_url"], "oauth")["resource"]
        client_id = self.db.query([caller, "client_id"], "oauth")["resource"]
        scopes = self.db.query([caller, "scopes"], "oauth")["resource"]
        params= {
                "client_id":client_id, # TODO: guide the user to get their own
                "response_type": "code",
                "redirect_uri": self.getselfurl(),
                "scope": ' '.join(scopes)
                }

        if "redirect_uri" not in params:
            params["redirect_uri"] = self.getselfurl()

        r = requests.get(auth_url, params=params)
        loginurl = r.url
        self.logger(f"Please follow this link and login to your account.\n{loginurl}")
        self.hostserver()
        token = self.res
        return token


    def getaccesstoken(self):
        #if not self.watcher_loaded:
            #self.watcher = self.db.membase["classes"]["Watcher"]
            #self.watcher_loaded = True

        caller = self.db.caller_name()[0].lower()
        self.logger(f"accesstoken requested by {caller}")
        if self.db.query([caller, "access_token"], "oauth")["success"]:
            if self.checkvalid(caller):
                accesstoken = self.db.query([caller, "access_token"], "oauth")["resource"]
            else:
                self.logger(f"Refreshing token for {caller}")
                accesstoken = self.refreshtoken(caller)
            return accesstoken

        accessurl = self.db.query([caller, "access_url"], "oauth")["resource"]
        client_id = self.db.query([caller, "client_id"], "oauth")["resource"]
        client_secret = self.db.query([caller, "client_secret"], "oauth")["resource"]

        data = {
            "grant_type": "authorization_code",
            "redirect_uri": self.getselfurl(),
            "code": self.getauthorized(caller),
            "client_id": client_id,
            "client_secret": client_secret
        }

        headers = {
            "Authorization": "Basic"
        }

        r = requests.post(accessurl, data=data)
        res = r.json()
        extime = int(res["expires_in"]) + int(time.time())
        writedata = {"access_token": res["access_token"], "refresh_token":res["refresh_token"], "expires_on": extime}
        self.db.write(caller, writedata, "oauth")
        return res["access_token"]

    def checkvalid(self, caller):
        # check if refresh date has passed
        expires_on = self.db.query([caller, "expires_on"], "oauth")["resource"]
        if expires_on > int(time.time()): # still valid
            return True
        return False

    def refreshtoken(self, caller):
        client_id = self.db.query([caller, "client_id"], "oauth")["resource"]
        client_secret = self.db.query([caller, "client_secret"], "oauth")["resource"]
        refresh_token = self.db.query([caller, "refresh_token"], "oauth")["resource"]

        refresh_url = self.db.query([caller, "refresh_url"], "oauth")["resource"]
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token
        }
        
        headers = {
            "Authorization": f"Basic"
        }
        r = requests.post(refresh_url, data=data)
        res = r.json()
        extime = int(res["expires_in"]) + int(time.time())
        writedata = {"access_token": res["access_token"],"expires_on": extime}
        if "refresh_token" in res:
            writedata["refresh_token"] = res["refresh_token"]
        self.db.write(caller, writedata, "oauth")
        return res["access_token"]

    def getselfurl(self):
        #STUB
        return "http://83.163.109.161:8000/callback"

    def hostserver(self):
        """host server to receive callback from oauth service"""
        #TODO: check if own ip is reachable from the outside world
        #TODO: if so, check if website module is available. if it is, use it's callback page. if not, host your own.
        #TODO: catch callback and return.
        

        WEBSITE = False
        if not WEBSITE:
            from flask import Flask, request
            app = Flask(__name__)

            @app.route("/callback")
            def hello_world():
                self.res = request.args.get("code")
                #print(self.res)
                #return "<p>You've logged in succesfully</p>"
                func = request.environ.get('werkzeug.server.shutdown')()
                return "<p>You've logged in succesfully</p>"

            app.run(host='0.0.0.0', port=8000)
        return self.res
