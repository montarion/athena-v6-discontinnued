from flask import Flask, render_template, safe_join, send_from_directory
from flask_sockets import Sockets

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

import os


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

    def startrun(self):
        staticfolder = os.path.join(self.basefolder, "static")
        tmpfolder = os.path.join(self.basefolder, "templates")
        self.app = Flask(__name__, static_folder=staticfolder, template_folder=tmpfolder)
        self.socket = Sockets(self.app)

        self.logger("website is running")

        @self.app.route("/")
        def hello():
            return render_template("index.html")


        @self.app.route("/templates/<path:size>/<path:location>/<path:filename>")
        def template(location, filename, size):
            tmppath = os.path.abspath(f"data/modules/{location}/templates/{size}")
            if filename.split(".")[-1] in ["css"]:
                finpath = safe_join(tmppath, filename)
                self.logger(tmppath)
                return send_from_directory(tmppath, filename)
            if filename.split(".")[-1] == "js":
                return send_from_directory(tmppath, filename, mimetype = "text/javascript")
            else:
                return 404

        server = pywsgi.WSGIServer(('0.0.0.0', 8080), self.app, handler_class=WebSocketHandler)
        server.serve_forever()
