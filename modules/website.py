from flask import Flask, render_template, safe_join, send_from_directory, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, current_user, login_user, logout_user, fresh_login_required
from flask_assets import Environment, Bundle
from flask_compress import Compress
from time import sleep
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
# for debugging
from werkzeug.serving import run_with_reloader
from werkzeug.debug import DebuggedApplication

import os, json
# source for  the goodgood: https://gist.github.com/danielfennelly/9a7e9b71c0c38cd124d0862fd93ce217

from components.logger import Logger
DEBUG = True
# For flask_login
class User(UserMixin):
    def __init__(self):
        self.auth = False

    """
    @property
    def is_authenticated(self):
        return self.auth
    """
class Website:
    def __init__(self, Networking=None, Watcher=None, Database=None):
        self.dependencies = {"tier": "user", "dependencies":["Networking", "Watcher", "Database"]}
        self.characteristics= ["blocking"]
        self.capabilities = ["website", "ui", "input", "question"]

        #self.timing = {"unit": "minutes", "count":2}
        self.networking = Networking
        self.watcher = Watcher
        self.db = Database

        self.logger = Logger("Website").logger

        self.basefolder = os.path.abspath("data/modules/website/")

        # other init stuff happens in startrun

    def detecttemplates(self):
        # detect other ui elements
        pass

    def question(self, question):
        pass
    def query(self, query, connectionID = 666):
        """connectionID is the id of who is asking(starts at 0, database is 999)
           the query is a dict containing the following keys:
            "category", "type", "data", "metadata"
        """
        category = query["category"]
        qtype = query["type"]
        qdata = query.get("data", None)
        qmetadata = query.get("metadata", None)
        response = {}
        if category == "admin":
            if qtype == "signup":
                self.logger(qdata)
                resdata = {"success":True, "code":200}
                response = {"category": "admin", "type": "signup", "data": resdata}
            if qtype == "login":
                pass
            if qtype == "enabled_mods":
                #TODO: Get list of enabled modules that the website can display
                # hardcoded for now
                moduledict = {
                            "Anime":{"standard":
                                {"category": "request", "type": "lastshow"}
                            },
                            "Weather":{"standard":
                                {"category": "request", "type": "current"}
                            },
                            "Monitor":{"standard":
                                {"category": "request", "type": "basic"}
                            }
                            }
                response = {"category": "admin", "type": "enabled_mods", "data": moduledict}
        if category == "request":
            if qtype == "template":
                """ get template data for presets """
                self.logger("template request")
                #self.logger(query)
                preset = qdata["preset"] # e.g. weather
                files = qdata["filenames"] # e.g. weather.html
                elementsize = qdata["size"] # either small or big(for expanded card)
                metadata = qmetadata
                if "copy" in metadata:
                    self.logger(metadata["copy"])
                    newmeta = metadata["copy"]
                    metadata = newmeta

                try:
                    tmppath = os.path.abspath(f"data/modules/{preset}/ui/website/templates/{elementsize}")
                    finres = {}
                    for filename in files:
                        extension = filename.split(".")[-1]
                        #self.logger(extension, "info", "blue")
                        if extension in ["js", "html", "json"]:
                            finpath = os.path.join(tmppath, filename)
                            with open(finpath) as f:
                                result = f.read()
                            if extension == "json":
                                result = json.loads(result)
                            finres[filename] = result
                    #self.logger(finres, "alert")
                    response = self.networking.messagebuilder("web", "template", finres, metadata)
                except Exception as e1:
                    self.logger(f"Error: {str(e1)}")
                    data = {"status": 404}
                    returnmsg = self.networking.messagebuilder(category, qtype, qdata, metadata)
                    self.logger(f"Returning: {returnmsg}")
                    response = returnmsg


        # TODO: Read out the query
        # TODO: Use it to write out the response
        #self.logger(response, "debug", "blue")
        return response

    def startrun(self):
        staticfolder = os.path.join(self.basefolder, "static")
        tmpfolder = os.path.join(self.basefolder, "templates")
        self.app = Flask(__name__, static_folder=staticfolder, template_folder=tmpfolder)
        self.app.secret_key = "haaaaaaaaaaaaai"
        self.app.config['TRAP_BAD_REQUEST_ERRORS'] = True
        self.assets = Environment(self.app)
        js = Bundle(
            "scripts/networking.js", "scripts/ui.js", 
            "scripts/images.js", "scripts/images.js", 
            "scripts/text.js", "scripts/main.js",
            output="scripts/packed.js"
        )
        self.assets.register("js_all", js)
        self.login_manager = LoginManager()
        self.login_manager.init_app(self.app)
        self.login_manager.login_view = "login"
        Compress(self.app)
        ssl_enabled = True

        @self.app.route("/")
        @fresh_login_required
        def index():
            return render_template("index.html")


        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            if request.method == 'GET':
                return render_template("login.html")

            storedpasswd = self.db.query(["web-ui", "password"], "credentials")["resource"]
            if request.form['password'] == storedpasswd:
                user = User()
                user.auth= True
                user.id = 1
                login_user(user)
                return redirect(url_for('index'))


            return 'Bad login'

        @self.app.route('/webauthn', methods=['GET'])
        def webauth():
            return render_template("webauthn.html")

        @self.app.route('/bluetooth', methods=['GET'])
        def btserial():
            return render_template("bluetooth.html")

        @self.app.before_request
        def before_request():
            if not request.is_secure and ssl_enabled:
                self.logger("Redirecting request to https: {request.url}", "alert", "red")
                url = request.url.replace('http://', 'https://', 1)
                code = 301
                return redirect(url, code=code)

        @self.app.route("/templates/<path:size>/<path:location>/<path:filename>")
        def template(location, filename, size):
            tmppath = os.path.abspath(f"data/modules/{location}/ui/website/templates/{size}")
            if filename.split(".")[-1] in ["css"]:
                finpath = safe_join(tmppath, filename)
                self.logger(tmppath)
                return send_from_directory(tmppath, filename, mimetype = "text/css")
            if filename.split(".")[-1] == "js":
                return send_from_directory(tmppath, filename, mimetype = "text/javascript")
            else:
                return 404


        @self.login_manager.user_loader
        def user_loader(id):
            user = User()
            user.id = self.db.query("name", "personalia")["resource"]
            return user

        # check if tls/ssl is available
        ssl_enabled = self.db.query(["ssl_enabled"], "system")["resource"]

        # check if debug requested
        if DEBUG:
            self.app = DebuggedApplication(self.app)
        if ssl_enabled:
            certchain_location = self.db.query(["certchain"], "system")["resource"]
            keyfile_location = self.db.query(["keyfile"], "system")["resource"]
            server = pywsgi.WSGIServer(('0.0.0.0', 8080), self.app, handler_class=WebSocketHandler, keyfile=keyfile_location, certfile=certchain_location)
            self.logger("Using SSL")
        else:
            server = pywsgi.WSGIServer(('0.0.0.0', 8080), self.app, handler_class=WebSocketHandler)
            self.logger("Not using ssl. Connection is insecure")

        self.logger("Website is running.")
        server.serve_forever()
