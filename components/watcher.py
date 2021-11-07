import json, threading, inspect
from components.logger import Logger
from time import sleep
from pubsub import pub

class Watcher:
    def __init__(self, Database, classobjdict):
        self.logger = Logger("Watcher").logger
        self.dbobj = Database
        self.logger(self.dbobj)
        self.classobjdict = classobjdict

        self.listenstop = False
        self.trigfound = False
        self.subscriptions = []
        self.classdict = {}
        self.funcdict = {}
        self.senddict = {}
        self.triggerdict = {}



    def getclass(self, classname):
        self.classobjdict = self.dbobj.membase["classes"]
        if classname in self.classobjdict:
            return {"resource": self.classobjdict[classname], "status": 200, "success": True}
        else:
            self.logger("class not found")
            return {"resource": "Class not found", "status": 404, "success": False} 


    def execute(self, classname, funcname, args={}, threaded=False):
        self.logger("inside execute function")
        database = self.getclass("Database")
        if type(classname) == str:
            classobj = self.getclass(classname)
            if not classobj["success"]:
                self.logger("Class not found.")
                return "Class not found"
            classobj = classobj["resource"]
        else:
            classobj = classname
        self.logger(f"classname: {classobj}")
        self.logger(f"funcname: {funcname}")
        if funcname:
            # do things with class object
            if threaded:
                threading.Thread(target=getattr(classobj(database), funcname), kwargs=args).start()
            else:
                res = getattr(classobj, funcname)(**args)
                return res




    def listen(self, data):
        self.logger(data, "alert" , "blue")
        channel = data["channel"]
        data = data["data"]
        self.logger(f"Got message for: {channel}")
        self.logger(f"Message: {data}")

        if channel in self.senddict.keys():
            targetlist = self.senddict[channel]
            nw = self.getclass("Networking")["resource"]
            nw.regsend(data, targetlist)

    def register(self, sublist, target, listener=None):
        if not listener:
            listener = self.listen
        for channel in sublist:
            if channel not in self.senddict:
                self.senddict[channel] = []
            self.senddict[channel].append(target)
        
            pub.subscribe(listener, channel)

    def publish(self, channel, data:dict):
        """
            Allows every class to publish without importing pubsub.
            Usage: Watcher().publish(Foo() / "Foo", {"bar": "argumentcontent"}
            Note: using the class so that you can pass "self" from within the module.
                if using a string
        """

        if type(channel) != str: # convert to string if class was used
            channel = channel.__class__.__name__

        realdata = {}
        realdata["channel"] = channel
        realdata["data"] = data
        pub.sendMessage(channel, data=realdata)


    def getresult(self, regdata):
        """
            Allows one to get the result from any specific function.
            Usage: regdata = {'trigger':{'class':'foo', 'function':'functorun()', 'args':{'foo':'bar},
                             'result':{'class':Bar(), 'function':'funcname', 'args':{'foo':'bar'}}

            trigger[class] is the name of the class you want updates from.
            trigger[args] are the arguments that are sent to the functorun
            result[class] is class object(self in a class) that you want to call when triggered
            arg keys must match the name of the parameter.

        """
        pass


