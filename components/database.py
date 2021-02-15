from ast import literal_eval as eval
from components.logger import Logger
import json, traceback, inspect, shortuuid, random
from filelock import FileLock
from time import sleep
class Database:
    membase = {}
    def __init__(self, Networking=None):
        self.logger = Logger("DATABASE").logger
        self.db = ('data/db.json')
        self.table = "main"
        self.nw = Networking
        self.membase = Database.membase
        self.userresponse = {}
        self.dblock = FileLock(self.db+".lock")

    def getdbfile(self, editableonly = False, rohidden = True):
        with self.dblock:
            with open(self.db) as f:
                tables = json.loads(f.read())
        
        tabledict = {}
        for table in tables:
            rolist = tables[table].get("readonly", [])
            tabledict[table] = {}
            for key in tables[table]:
                if rohidden:
                    if key == "readonly":
                        continue
                if editableonly:
                    if key in rolist:
                        continue
                value = tables[table][key]
                tabledict[table][key] = value
            if len(tabledict[table]) == 0:
                del tabledict[table]
        
        return tabledict

    def write(self, key, value, table=None, readonly = False, update =True):
        """Usage: Database().write("foo", {"foo":"bar"}, "test")"""
        #self.logger("Writing..")
        # fix datatypes
        key = json.loads(json.dumps(key))
        if type(key) != str:
            key = str(key)
        value = json.loads(json.dumps(value))

        if table:
            self.table = table

        #t = self.gettable(table)
        fulldata = self.getdbfile(rohidden=False)
        tables = fulldata.keys()

        if table not in tables:
            fulldata[table] = {}


        # save readonly data if it exists
        rodata = []
        if "readonly" in fulldata[table]:
            rodata = fulldata[table]["readonly"]

        data = json.loads(json.dumps(fulldata[table]))

        data["readonly"] = rodata
        #self.logger(f"old data: {fulldata[table]}", "debug", "blue")

        if update: # in case you want to update lists
            if type(data[key]) == list:
                data[key].append(value)
            else:
                data[key] = value
        else:
            data[key] = value # add actual data
        if readonly:
            if "readonly" not in data:
                data["readonly"] = []
            data["readonly"].append(key)
        # save in proper form
        fulldata[table] = data
        #self.logger(f"new data: {data}", "debug", "blue")

            # write fulldata to dict
        with open(self.db, "w") as f:
            json.dump(fulldata, f, indent=4)


    def query(self, query, table=None):
        """Usage: Database().query("name", "test")"""
        # called by(test)
        #callerclass, callerfunc = self.caller_name() 
        #self.logger(f"Query requested by: {callerclass, callerfunc}", "debug", "yellow")
        
        if table:
            self.table = table
        fulldata = self.getdbfile()

        try:
            """
            fulldata = ""
            while len(fulldata) == 0:
                with open(self.db) as f:
                    
                    try:
                        fulldata = json.loads(f.read())
                    except:
                        for i in range(0,10):
                            self.logger(i, "debug", "red")
                            sleep(random.randint(70,100)/100)
                            try:
                                fulldata = json.loads(f.read())
                            except:
                                pass
            """
            data = fulldata[table]
            if type(query) == list: #e.g. ..query(["lastshow", "title"])
                for q in query:
                    data = data[q]
                result = data
            else:
                result = data[query]

            if type(result) == str:
                try:
                    result = eval(result)
                except:
                        pass
            #self.logger(f"result: {result} - {type(result)}", "debug", "red")

            msg = {"status": "200", "resource":result}
            return msg
        except KeyError as e:
            # ask question
            callerclass, callerfunc = self.caller_name()
            self.logger(f"Query for \"{query}\" in table: {table} requested by: {callerclass, callerfunc}", "debug", "yellow")
            questionlist = [{"type": "text", "question": f"{query}"}]

            try: 
                answer = self.getfromuser(questionlist)
                realanswer = answer["data"]["answer"] 
                self.write(query, realanswer, self.table)
                self.logger(f"written answer to database.") 
                if type(realanswer) == str:
                    try:
                        realanswer= eval(realanswer)
                    except:
                        pass
                #self.logger(f"result: {realanswer} - {type(realanswer)}")
                res = {"status": "201", "resource":realanswer}
            except Exception as e3:
                self.logger(f"Error when asking user. {str(e3)}", "alert", "red")
                traceback.print_exc()
                # TODO: implement timeout function
                res = {"status": "404", "resource": f"Query: \"{query}\" not found"}
            return res

    def remove(self, query, table=None):
        """NOT IMPLEMENTED"""
        #TODO: IMPLEMENT
        if table:
            self.table = self.db.table(table)

        fulldata = self.getdbfile()
        """
        fulldata = ""
        while len(fulldata) == 0:
            with open(self.db) as f:
                # get data
                fulldata = json.loads(f.read())
        """

        tables = fulldata.keys()
        if table not in tables:
            fulldata[table] = {}

        data = fulldata[table]

        # remove data
        del data[key]

        # save in proper form
        fulldata[table] = data

        # write fulldata to dict
        with open(self.db, "w") as f:
            json.dump(fulldata, f, indent=4)


    def gettable(self, table):
        """Usage: Database().gettable("table")"""

        fulldata = self.getdbfile()
        """
        fulldata = ""
        while len(fulldata) == 0:
            with open(self.db) as f:
                # get data
                try:
                    fulldata = json.loads(f.read())
                except:
                    for i in range(0,4):
                        self.logger(i, "debug", "red")
                        sleep(random.randint(30,70)/100)
                        try:
                            fulldata = json.loads(f.read())
                        except:
                            pass
        """
        try:
            table = fulldata[table]
            res = {"status": 200, "resource": table}
        except KeyError:
            try: #create it
                table = {}
                fulldata[table] = {}
                res = {"status": 200, "resource": table}
            except:
                res = {"status": 404, "resource": f"table: \"{table}\" not found"}
        #self.logger(res, "debug", "yellow")
        return res

    def gettables(self):
        fulldata = self.getdbfile()
        tables = list(fulldata.keys())
        res = {"status": 200, "resource": tables}
        return res

    def geteditable(self):
        tables = self.getdbfile(True)
        res = {"status": 200, "resource": tables}
        return res

    def getfromuser(self, questionlist):
        """gets answer from user for given question. can only do one question at a time for now"""
        asker = self.caller_name(3)
        # stop execution
        # TODO: stop scheduled execution .. you don't have to, nothing will advance while waiting though
        taskclass = self.membase["classes"]["Tasks"]
        self.logger(taskclass)
        taskclass.pause(asker[0])

        ui_interfaces = self.membase["ui-interfaces"]
        self.logger(ui_interfaces, "alert", "green")
        # choose the best ui
        # hardcoded to website for now
        bestui = "Website"
        if bestui == "Website":
            bestuiuser = "website"
            # write down somewhere that website requires networking
            realquestionlist = {}
            self.logger(questionlist)
            for q in questionlist:
                realquestionlist[q["type"]] = q["question"]

            for q in realquestionlist:
                finq = {"asker":asker, "question":realquestionlist[q]}
                #create guid
                guid = shortuuid.uuid()[:8]
                msg = {"category":"question", "type":"text", "data":finq,"metadata": {"copy":{"guid":guid}}}


                self.logger(self.membase["classes"], "debug", "blue")
                # get network class
                networking = self.membase["classes"]["Networking"]
                self.logger(networking)
                # get watcher class
                watcher = self.membase["classes"]["Watcher"]

                # send to website

                ui_id = networking.findtarget(bestuiuser)
                self.logger(ui_id)

                # register yourself with watcher
                regdata = {"trigger":{"class":"Networking"}, "result":{"class": self, "function":"responsewait"}}
                watcher.register(regdata)

                # send message
                networking.regsend(msg, ui_id)

                # wait for your answer to come in
                while True:
                    if self.userresponse.get("category", None) == "answer": # response looks like: {"category":"answer", "type":"text", "data":{"answer":"('52.090', '5.232')"}, "metadata":{"guid": "QonSPv29"}};
                        if self.userresponse["metadata"].get("guid") == guid:
                            # TODO: unsubscribe from networking
                            break
                    sleep(0.5)
                del self.userresponse["metadata"]["guid"]

                # start schedule again
                taskclass.resume(asker[0])
                return self.userresponse


    def responsewait(self, **args):
        self.userresponse = args
        self.logger(f"response arguments! - {args}")

    def caller_name(self, skip=2):
        """from https://gist.github.com/techtonik/2151727 """
        stack = inspect.stack()
        start = 0 + skip
        if len(stack) < start + 1:
          return ''
        parentframe = stack[start][0]    

        name = []
        module = inspect.getmodule(parentframe)
        if module:
            name.append(module.__name__)
        # detect classname
        if 'self' in parentframe.f_locals:
            name.append(parentframe.f_locals['self'].__class__.__name__)
        codename = parentframe.f_code.co_name
        if codename != '<module>':  # top level usually
            name.append( codename ) # function or a method
        del parentframe
        for i in name:
            if "." in i:
                name.remove(i)
        return name

    def messagebuilder(self, category, msgtype, data={}, metadata={}):
        msg = json.dumps({"category":category, "type":msgtype, "data":data, "metadata":metadata})
        return msg

    def getmoduledata(self, modulename):
        """Gets json data for specific ui from a supporting module's metadata.json
           Usage: database().getmoduledata('Anime')"""
        x = 2
        while True: # loop because it might be called from a different class, by the right one
            callerclass, _ = self.caller_name(x)
            if callerclass in self.membase["ui-interfaces"].keys():
                break
            else:
                x += 1
        fileloc = f"data/modules/{modulename}/ui/{callerclass.lower()}/metadata.json"
        with open(fileloc) as f:
            data = json.loads(f.read())
        return data
