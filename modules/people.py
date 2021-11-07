from components.logger import Logger
import os, pwd, json
from pathlib import Path

class People:
    def __init__(self):
        self.dependencies = {"tier":"user", "dependencies":[]}
        self.characteristics= ["standalone"]
        self.capabilities = ["social", "information"]
        # do not add init stuff
        self.logger = Logger("People").logger
        self.datapath = f"data/modules/{self.__class__.__name__.lower()}"


    def dostuff(self):
        pass

    def query(self, query, connectionID = 666):
        """connectionID is the id of who is asking(starts at 0, database is 999)
           the query is a dict containing the following keys:
            "category", "type", "data", "metadata"
        """
        category = query["category"]
        qtype = query["type"]
        qdata = query.get("data", None)
        metadata = query.get("metadata", None)

        response = {}
        if category == "get":
            if qtype == "full":
                name = qdata["name"]
                person = self.getdata(name)
                response[name] = person
            if qtype == "argument":
                name = qdata["name"]
                args = qdata["args"]
                person = self.getdata(name, args)
                response[name] = person
        # TODO: Read out the query
        # TODO: Use it to write out the response
        return response

    def getdata(self, name, argument=None):
        """get data on a person"""
        # first find it
        base = "/home/pi/.people/"
        path = ""
        for p in Path(base).rglob(f"*{name}"):
            path = p

        res = {}
        res["files"] = os.listdir(path)
        res["path"] = os.path.join(base, path)
        res["data"] = self.readfile(path, argument)
        return res

    def readfile(self, path, args=None):
        filepath = ""
        for p in Path(path).rglob(f"file.json"):
            filepath = p
        with open(filepath) as f:
            data = json.load(f)

        if args:
            res = {}
            for argument in args: 
                res[argument] = "Not found"
                if argument in data:
                    res[argument] = data[argument]
                else:
                    for k in data.keys():
                        if type(data[k]) == dict:
                            if argument in data[k]:
                                res[argument] = data[k][argument]
        else:
            res = data
        return res

    def writedata(self, name, data):
        base = "/home/pi/.people/"
        path = None
        for p in Path(base).rglob(f"*{name}"):
            path = p
        if not path:
            os.mkdir(f"{base}{name}")
            path = f"{base}{name}/file.json"
            with open(path, "w") as f:
                json.dump(data, f)
        else:
            if not os.path.isfile(f"{path}/file.json"):
                with open(f"{path}/file.json", "w") as f:
                    json.dump({},f)
            with open(f"{path}/file.json", "r+") as f:
                fdata = json.load(f)
                for k,v in data.items():
                    fdata[k] = v
                f.seek(0)
                json.dump(fdata, f, indent=4)
        self.logger(f"Wrote to {path}")
