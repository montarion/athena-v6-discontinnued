# moving to sqlite
from ast import literal_eval as eval
from components.logger import Logger
import json, traceback, inspect, shortuuid, random, os
import sqlite3
from sqlitedict import SqliteDict
from time import sleep
class Database:
    def __init__(self, Networking=None):
        self.logger = Logger("DATABASE").logger
        datadir = "/home/pi/code/athena/data"
        self.db = os.path.join(datadir, "main.db")
        self.table = "main"
        self.nw = Networking
        self.userresponse = {}
        with SqliteDict(":memory:", autocommit=True, encode=json.dumps, decode=json.loads) as dbdict:
            self.membase = {}
    def gettable(self, table):
        res = ""
        try:
            with SqliteDict(self.db, encode=json.dumps, decode=json.loads) as dbdict:
                res = dbdict[table]
            msg = {"status": "200", "resource":res, "success": True}
            return msg
        except:
            res = {"status": 404, "resource": f"table: \"{table}\" not found", "success": False}
            return msg

    def write(self, key, value, table, readonly = False, update =True):
        """Usage: Database().write("foo", {"foo":"bar"}, "test")"""
        #self.logger("Writing..")
        # fix datatypes
        key = json.loads(json.dumps(key))
        if type(key) != str:
            key = str(key)
        value = json.loads(json.dumps(value))

        with SqliteDict(self.db, encode=json.dumps, decode=json.loads) as dbdict:
            if table not in dbdict.keys():
                dbdict[table] = {}
                self.logger(f"created table: {table}", "debug")
                dbdict.commit()

            tdict = dbdict[table]
            

            if key not in tdict: # can't update something that doesn't exist, so check first
                update = False
            if update:
                if type(tdict[key]) == list:
                    tdict[key].append(value)
                elif type(value) == dict:
                    for k,v in value.items():
                        tdict[key][k] = v
            else:
                tdict[key] = value # add actual data

            dbdict[table] = tdict # save back into dbdict
            dbdict.commit() # then commit

    def query(self, query, table):
        """Usage: 
            Database().query("city", "personalia") or:
            Database().query(["lastshow", "title"], "anime")
        """
        # called by(test)
        #callerclass, callerfunc = self.caller_name() 
        #self.logger(f"Query requested by: {callerclass, callerfunc}", "debug", "yellow")
        
        try:
            res = ""
            with SqliteDict(self.db, encode=json.dumps, decode=json.loads) as dbdict:
                data = dbdict[table]
                if type(query) == str:
                    query = [query]
                if type(query) == list: #e.g. ..query(["lastshow", "title"])
                    for q in query:
                        data = data[q]
                    res = data
            msg = {"status": "200", "resource":res, "success": True}
            return msg
        except KeyError as e:
            """
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
            """
            res = {"status": "404", "resource": f"Query: \"{query}\" not found", "success": False}
            return res
    def remove(self, query, table=None):
        """NOT IMPLEMENTED"""
        #TODO: IMPLEMENT

    def gettable2(self, table):
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
            res = {"status": 200, "resource": table, "success": True}
        except KeyError:
            self.logger("Couldn't create table, trying to create.", "debug")
            try: #create it
                fulldata[table] = {}
                self.logger("Creation successful", "debug")
                res = {"status": 200, "resource": table, "success": True}
            except Exception as e:
                self.logger(f"Creation failed. Reason:\n{e}", "alert")
                res = {"status": 404, "resource": f"table: \"{table}\" not found", "success": False}
        #self.logger(res, "debug", "yellow")
        return res

    def gettables2(self):
        fulldata = self.getdbfile()
        tables = list(fulldata.keys())
        res = {"status": 200, "resource": tables, "success": True}
        return res

    def getfromuser(self, questionlist):
        """gets answer from user for given question. can only do one question at a time for now"""
        asker = self.caller_name(3)
        # stop execution
        # TODO: stop scheduled execution .. you don't have to, nothing will advance while waiting though
        taskclass = self.membase["classes"]["Tasks"]
        self.logger(taskclass)
        taskclass.pause(asker[0])

        ui_interfaces = self.membase["ui-interfaces"].keys()
        self.logger(ui_interfaces, "alert", "green")
        # choose the best ui
        # hardcoded to website for now
        currentui = self.query("current_ui", "system")
        if not currentui["success"]:
            currentui = self.query("primary_ui", "system")
        self.logger(currentui)
        currentui = currentui["resource"]
        self.logger(currentui)
        if currentui == "discord":
            answer = self.membase["classes"]["Watcher"].execute("Discord", "question", {"question": questionlist[0]})


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
            if i == "__main__":
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
            callerclass, callerfunc = self.caller_name(x)
            if callerclass.lower() in self.membase["ui-interfaces"]["support"].keys():
                break
            else:
                x += 1
        fileloc = f"data/modules/{modulename}/ui/{callerclass.lower()}/metadata.json"
        with open(fileloc) as f:
            data = json.loads(f.read())
        return data

    def findtarget(self, query):
        idlist = []
        self.logger(f"searching for {query}", "debug")
        res = self.gettable("connections")
        for key in res["resource"]:
            dic = res["resource"]
            for user in dic:
                userdata = dic[user]
                for val in userdata.values():
                    if type(val) == int  or type(query) == int:
                        searchres = query == val
                    else:
                        searchres = query in val
                    if searchres:
                        idlist.append(dic[key]["id"])

        return {"success": True, "resource": idlist, "status":200}
