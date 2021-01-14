import websockets, asyncio, json, os, tracemalloc, shortuuid
from components.logger import Logger
class Networking:

    def __init__(self, database=None):
        self.db = database
        self.logger = Logger("Networking").logger
        self.watcher_loaded = False

    async def runserver(self, websocket, path):
        self.logger("got new client!", "alert", "yellow")
        while True:
            try:
                data = await websocket.recv()
                msg = json.loads(data)
                await self.msghandler(websocket, msg)
                await asyncio.sleep(0.1)
            except ConnectionResetError as e1:
                self.logger("Reset error", "alert", "red")
                await asyncio.sleep(2)
                raise ConnectionResetError
                break
            except Exception as e2:
                # use re for error parsing
                if "1001" in str(e2) or "1005" in str(e2):
                    #self.logger(f"Error: {str(e2)}", "alert", "red")
                    await websocket.close()
                    self.logger("closed.")
                    break
                else:
                    self.logger(str(e2))
                    await websocket.close()
                    break

    def createid(self): 
        table = self.db.gettable("users") 
        if table["status"] == 200:
            curid = len(table)
            newid = curid + 1
            return int(newid)
        else:
            return table

    def findtarget(self, query):
        idlist = []
        self.logger(f"searching for {query}", "debug")
        res = self.db.gettable("users")
        for key in res["resource"]:
            dic = res["resource"]
            searchres = query in dic[key].values()
            if searchres:
                idlist.append(dic[key]["id"])
        return idlist

    def regsend(self, message, targetidlist):
        loop = self.db.membase["eventloop"]
        self.logger("Sending through regsend")
        uuid = shortuuid.uuid()[:4]
        self.senddict[uuid] = {}
        self.senddict[uuid]["message"] = message
        self.senddict[uuid]["targetidlist"] = targetidlist
        self.logger(self.senddict)
        return True

    async def send(self, message, targetidlist):
        loop = self.db.membase["eventloop"]
        self.logger("Sending through regsend")
        uuid = shortuuid.uuid()[:4]
        self.senddict[uuid] = {}
        self.senddict[uuid]["message"] = message
        self.senddict[uuid]["targetidlist"] = targetidlist

    async def realsend(self):
        self.senddict = {}
        self.logger(self.senddict)
        while True:
            #self.logger("checking...")
            #self.logger(self.senddict)
            for k in self.senddict.keys():
                self.logger("sending...")
                msg = self.senddict[k]["message"]
                targetidlist = self.senddict[k]["targetidlist"]
                returnmsg = {"success": [], "failure": []}
                for targetid in targetidlist:
                    socket = self.db.membase[targetid]["socket"]
                    if type(msg) == dict:
                        msg = json.dumps(msg)
                    await socket.send(msg)
                returnmsg["success"].append(targetid)
            self.senddict = {}
            await asyncio.sleep(0.2)

        #return returnmsg

    async def msghandler(self, websocket, msg):
        if not self.watcher_loaded:
            self.watcher = self.db.membase["classes"]["Watcher"]
            self.watcher_loaded = True
        category = msg["category"]
        type = msg["type"]
        data = msg.get("data", {})
        metadata = msg.get("metadata", {})
        # always check for guid
        if "copy" in metadata:
            self.logger(metadata["copy"])
            newmeta = metadata["copy"]
            metadata = newmeta

        if category == "admin":
            if type == "signin":
                name = data["name"]
                self.logger("received signin")
                self.logger(data.keys())
                if "id" in data.keys():
                    id = data["id"]
                    self.logger(f"already has id: {id}")
                else:
                    #create new id
                    id = self.createid()
                self.db.membase[id] = {"socket": websocket}
                self.db.write(id, {"id":id, "name": name}, "users")
                returnmsg = json.dumps({"category":"admin", "type":"signinresponse", "data":{"id":id}})
                await self.send(returnmsg, [id])

        if category == "test":
            self.logger("got test message", "debug", "yellow")
            if type == "web":
                self.logger("got web message")
                self.logger(msg)

                id = self.createid()
                self.logger(id)
                name = "website"
                self.db.membase[id] = {"socket": websocket}
                self.db.write(id, {"id":id, "name": name}, "users")
                data = {"id": id}
                returnmsg = self.messagebuilder("admin", "signinresponse", data, metadata)
                await websocket.send(returnmsg)

                # weather
                curdict = self.db.query("currentweather", "weather")

                if curdict["status"][:2] == "20":
                    data = curdict["resource"]

                    msg = self.messagebuilder("weather", "current", data, metadata)
                    await websocket.send(msg)

                #await asyncio.sleep(6)
                # anime
                curdict = self.db.query("lastshow", "anime")
                if curdict["status"][:2] == "20":
                    data = curdict["resource"]

                    msg = self.messagebuilder("anime", "lastshow", data, metadata)
                    await websocket.send(msg)

                # system monitor
                curdict = self.db.query("info", "monitor")
                if curdict["status"][:2] == "20":
                    data = curdict["resource"]

                    msg = self.messagebuilder("monitor", "info", data, metadata) # ! the category("monitor" here, MUST be the name of the folder in data/modules.)
                    await websocket.send(msg)

            if type == "question":
                questionlist = [{"type": "text", "question": "how are you doing?"}]
                self.db.getfromuser(questionlist)

        if category == "weather":
            if type == "current":
                self.logger("got request for weather")
                # run func
                self.logger("trying")
                #self.watcher.execute("Weather", "getcurrentweather")
                self.logger("done")
                curdict = self.db.query("currentweather", "weather")
                
                if curdict["status"][:2] == "20":
                    data = curdict["resource"]
                    msg = self.messagebuilder(category, type, data, metadata)
                    await websocket.send(msg)
                else:
                    returnmsg = {"status":404, "message":"couldn't find current weather"}
                    await websocket.send(json.dumps(returnmsg))
    
        if category == "anime":
            if type == "lastshow":
                # anime
                curdict = self.db.query("lastshow", "anime")
                if curdict["status"][:2] == "20":
                    data = curdict["resource"]

                    msg = self.messagebuilder("anime", "lastshow", data, metadata)
                    await websocket.send(msg)
            if type == "eplist":
                self.logger("GOT EPLIST REQUEST")
                title = data["title"]
                testlist = [{"size": 1280, "compressed":False, "episode":18},{"size": 350, "compressed":True, "episode":1},{"size": 1350, "compressed":False, "episode":11}, {"size": 1280, "compressed":False, "episode":16},{"size": 350, "compressed":True, "episode":3},{"size": 1350, "compressed":False, "episode":15}, {"size": 1280, "compressed":False, "episode":14},{"size": 350, "compressed":True, "episode":4},{"size": 1350, "compressed":False, "episode":22}]
                msg = self.messagebuilder(category, type, testlist, metadata)
                await websocket.send(msg)

        if category == "web":
            if type == "template":
                """ get template data for presets """
                self.logger("template request")
                self.logger(msg)
                data = msg["data"]
                preset = data["preset"] # e.g. weather
                files = data["filenames"] # e.g. weather.html
                elementsize = data["size"] # either small or big(for expanded card)
                metadata = msg["metadata"]
                if "copy" in metadata:
                    self.logger(metadata["copy"])
                    newmeta = metadata["copy"]
                    metadata = newmeta

                try:
                    tmppath = os.path.abspath(f"data/modules/{preset}/templates/{elementsize}")
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
                    data = finres
                    returnmsg = self.messagebuilder(category, type, data, metadata)
                    self.logger(f"Returning: {returnmsg}")
                    await websocket.send(returnmsg)
                except Exception as e1:
                    self.logger(f"Error: {str(e1)}")
                    data = {"status": 404}
                    returnmsg = self.messagebuilder(category, type, data, metadata)
                    self.logger(f"Returning: {returnmsg}")
                    await websocket.send(returnmsg)

        # maybe only do this bit if there's a flag set in membase, for security
        self.watcher.publish(self, msg)
        await asyncio.sleep(0.1)

    def messagebuilder(self, category, msgtype, data={}, metadata={}, target=None):
        msg = json.dumps({"category":category, "type":msgtype, "data":data, "metadata":metadata})
        if not target:
            return msg
        else:
            if target == "all":
                idlist = list(self.db.membase.keys())
            if type(target) == list:
                idlist = target
            elif type(target) == int:
                idlist = [target]

            result = {"success": [], "failure": []}

            for id in idlist:
                result = asyncio.get_running_loop().run_until_complete(self.send(msg, idlist))
            return result

    async def run_straglers(self):
        while True: 
            #pending = asyncio.all_tasks()
            #await asyncio.create_task(asyncio.gather(*pending))
            await asyncio.sleep(1)

    def startserving(self):
        self.logger("starting")
        tracemalloc.start()
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.db.membase["eventloop"] = self.loop
        serveserver = websockets.server.serve(self.runserver, "0.0.0.0", 8000)
        
        self.loop.create_task(self.run_straglers())
        #self.loop.run_until_complete(serveserver)
        asyncio.ensure_future(serveserver)
        self.loop.create_task(self.realsend())
        self.logger("waiting...")
        self.loop.run_forever()
        #TODO: FIX - THE WHILE LOOP INSIDE DATABASE().GETFROMUSER BLOCKS EVERYTHING. FIX. 
