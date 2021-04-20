from components.logger import Logger
import os, json, sys, hashlib
from time import sleep
class Filewatch:
    def __init__(self, Database=None):
        self.dependencies = {"tier":"user", "dependencies":["Database"]}
        self.characteristics= ["blocking"]
        self.capabilities = ["filewatch"]

        #self.timing = {"foo":"bar"} # sadly necessary for discovery process

        self.db = Database
        # do not add init stuff
    
    def register(self, filename, datadict):
        filedict = self.db.membase.get("filedict", {})
        # get caller, add to filedict
        caller = self.db.caller_name(2)[1]
        print(caller)
        if filename not in filedict.keys():
            filedict[filename] = {}
        filedict[filename][caller] = datadict
        self.db.membase["filedict"] = filedict
        return True

    def unregister(self, filename):
        filedict = self.db.membase.get("filedict", {})
        del filedict[filename]
        self.db.membase["filedict"] = filedict
        return True

    def watcher(self):
        changelist = []
        while True:
            
            filedict = self.db.membase.get("filedict", {})
            if len(filedict) == 0:
                sleep(10)
                continue
            md5 = hashlib.md5()
            for filename in filedict:
                for classname in filedict[filename]:
                    watchtype = filedict[filename][classname]["watchtype"]

                    if watchtype == "change":
                        with open(filename, 'rb') as f:
                            while True:
                                data = f.read(65536)
                                if not data:
                                    break
                                md5.update(data)

                        hash = md5.hexdigest()
                        print(hash)
                        if "hash" not in filedict[filename][classname]:
                            filedict[filename][classname]["hash"] = hash
                        else:
                            if filedict[filename][classname]["hash"] != hash:
                                filedict = self.respond(classname, filedict, filename)
                            else:
                                continue # nothing changed after all
                    elif watchtype == "create":
                        exists = os.path.isfile(filename)
                        if exists:
                            changelist.append(filename)
                            filedict = self.respond(classname, filedict, filename)
                    elif watchtype == "download":
                        filesize = os.stat(filename).st_size
                        filedict = self.respond(classname, filedict, filename, watchtype, size)

            # update filedict
            self.db.membase["filedict"] = filedict
            sleep(10)

    def respond(self, caller, filedict, filename, size=None):
        watchtype = filedict[filename][caller]["watchtype"]
        classname, function = filedict[filename][caller]["reportfunc"]["class"], filedict[filename][caller]["reportfunc"]["function"]

        if watchtype == "change":
            # run function with filename as parameter
            getattr(classname, function(filename))
            print(f"CHANGED: {filename}")
        elif watchtype == "create":
            # run function with filename as parameter, then remove
            print(f"CREATED: {filename}")
            getattr(classname, function(filename))
            del filedict[filename]
        elif watchtype == "download":
            # run function with filename as parameter. if size is same, remove but add finished:True
            finished = False
            filedict[filename]["oldsize"] = size
            if "oldsize" in filedict[filename].keys():
                if size == filedict[filename]["oldsize"]: # finished
                    finished = True
                    getattr(classname, function(filename, finished, size))
                    del filedict[filename]
                else: # still downloading
                    filedict[filename]["oldsize"] = size
                    getattr(classname, function(filename, finished, size))

        return filedict

    def startrun(self):
        """get dict of files(from membase), monitor them for changes.
           dict will look like: {"file.txt":{"hash": "jfkdlsjfds", "watchtype":"download|create|change", "reportfunc": Anime().downloaded}}
           
           "hash" will probably not be filled at the start """
        # init stuff..
        self.logger = Logger("Filewatch").logger
        self.datapath = f"data/modules/{self.__class__.__name__.lower()}"
        self.watcher()
        
