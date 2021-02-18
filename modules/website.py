from flask import Flask, render_template, safe_join, send_from_directory, request, redirect
from flask_sockets import Sockets
from time import sleep
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

import os, json


from components.logger import Logger

class Website:
    def __init__(self, Networking=None, Watcher=None, Database=None):
        self.dependencies = {"tier": "user", "dependencies":["Networking", "Watcher", "Database"]}
        self.capabilities = ["ui", "input", "blocking"]
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
        if query["category"] == "admin":
            if qtype == "signin":
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
                self.logger(query)
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
                        self.logger(extension, "info", "blue")
                        if extension in ["js", "html", "json"]:
                            finpath = os.path.join(tmppath, filename)
                            with open(finpath) as f:
                                result = f.read()
                            if extension == "json":
                                result = json.loads(result)
                            finres[filename] = result
                    self.logger(finres, "alert")
                    response = self.networking.messagebuilder("web", "template", finres, metadata)
                except Exception as e1:
                    self.logger(f"Error: {str(e1)}")
                    data = {"status": 404}
                    returnmsg = self.networking.messagebuilder(category, qtype, qdata, metadata)
                    self.logger(f"Returning: {returnmsg}")
                    response = returnmsg


        # TODO: Read out the query
        # TODO: Use it to write out the response
        self.logger(response, "debug", "blue")
        return response

    def startrun(self):
        staticfolder = os.path.join(self.basefolder, "static")
        tmpfolder = os.path.join(self.basefolder, "templates")
        self.app = Flask(__name__, static_folder=staticfolder, template_folder=tmpfolder)
        self.socket = Sockets(self.app)
        ssl_enabled = False

        self.logger("website is running")

        @self.app.route("/")
        def hello():
            return render_template("index.html")

        @self.app.before_request
        def before_request():
            if not request.is_secure and ssl_enabled:
                self.logger("Redirecting request to https: {request.url}", "alert", "red")
                url = request.url.replace('http://', 'https://', 1)
                code = 301
                return redirect(url, code=code)

        @self.app.route("/templates/<path:size>/<path:location>/<path:filename>")
        def template(location, filename, size):
            tmppath = os.path.abspath(f"data/modules/{location}/templates/{size}")
            if filename.split(".")[-1] in ["css"]:
                finpath = safe_join(tmppath, filename)
                self.logger(tmppath)
                return send_from_directory(tmppath, filename, mimetype = "text/stylesheet")
            if filename.split(".")[-1] == "js":
                return send_from_directory(tmppath, filename, mimetype = "text/javascript")
            else:
                return 404


        # check if tls/ssl is available
        ssl_enabled = self.db.query(["ssl_enabled"], "system")["resource"]
        if ssl_enabled:
            certchain_location = self.db.query(["certchain"], "system")["resource"]
            keyfile_location = self.db.query(["keyfile"], "system")["resource"]
            server = pywsgi.WSGIServer(('0.0.0.0', 8080), self.app, handler_class=WebSocketHandler, keyfile=keyfile_location, certfile=certchain_location)
            self.logger("Using SSL")
        else:
            server = pywsgi.WSGIServer(('0.0.0.0', 8080), self.app, handler_class=WebSocketHandler)
            self.logger("Not using ssl. Connection is insecure")

        server.serve_forever()
