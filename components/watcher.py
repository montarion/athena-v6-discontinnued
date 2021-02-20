import redis, json, threading, inspect
from components.logger import Logger
from time import sleep

class Watcher:
    def __init__(self, Database, classobjdict):
        self.logger = Logger("Watcher").logger
        self.r = redis.Redis(host='localhost', port=6379, db=0)
        self.p = self.r.pubsub(ignore_subscribe_messages=True)
        self.dbobj = Database
        self.logger(self.dbobj)
        self.classobjdict = classobjdict

        self.listenstop = False
        self.trigfound = False
        self.subscriptions = []
        self.classdict = {}
        self.funcdict = {}
        self.triggerdict = {}

    def startlisten(self):
        for x in self.subscriptions:
            self.p.subscribe(x)
        self.listenstop = False # allow execution
        if len(self.subscriptions) > 0:
            threading.Thread(target=self.listen).start()
            self.logger("started")
        else:
            self.logger("no subscriptions yet")

    def listen(self):
        while True:
            msg = self.p.get_message()
            if msg:
                #self.logger(msg)
                channel = msg["channel"].decode()
                data = msg["data"].decode()
                try:
                    data = json.loads(data)
                except Exception as e:
                    self.logger(e)
                self.logger(f"Got message for: {channel}")
                self.logger(f"Message: {data}")
                if channel in self.funcdict.keys():
                    channeldict = self.funcdict[channel]
                    trigger = channeldict["trigger"].get("returnvalue", None)
                    if type(trigger) != list:
                        triggerlist = [trigger]
                    else:
                        triggerlist = trigger

                    argdict = {}
                    for trigger in triggerlist:
                        if trigger in data.keys() or trigger == None:
                            # set flag
                            self.trigfound = True

                            # execute function
                            exec_class = channeldict["result"]["class"]
                            exec_func = channeldict["result"]["function"]
                            args = channeldict["result"].get("args", None)
                            if trigger == None:
                                argdict = data
                            else:
                                if args:
                                    for key, val in args.items():
                                        argdict[key] = data[val]
                                else:
                                    argdict[trigger] = data[trigger]
                    if self.trigfound:
                        t = getattr(exec_class, exec_func)(**argdict)
                        self.trigfound = False
            if self.listenstop:
                self.logger("Stopped listening for published messages.", "debug", "yellow")
                break

    def getclass(self, classname):
        self.classobjdict = self.dbobj.membase["classes"]
        if classname in self.classobjdict:
            return {"resource": self.classobjdict[classname], "status": 200}
        else:
            self.logger("class not found")
            return {"resource": "Class not found", "status": 404} 


    def execute(self, classname, funcname=None, args={}, threaded=False):
        self.logger("inside execute function")
        database = self.getclass("Database")
        if type(classname) == str:
            classobj = self.getclass(classname)
            self.logger(classobj)
            if not inspect.isclass(classobj):
                return "Class not found"
        else:
            classobj = classname
        self.logger(classobj)
        if funcname:
            # do things with class object
            if threaded:
                threading.Thread(target=getattr(classobj(database), funcname), kwargs=args).start()
            else:
                res = getattr(classobj(database), funcname(**args))
                return res
    def register(self, regdata):
        """
            Registers function to be ran when a specific other function is run/published
            Usage: regdata = {'trigger':{'class':'foo', 'returnvalue':'title'}, 
                             'result':{'class':Bar(), 'function':'funcname', 'args':{'foo':'bar'}}

            trigger[class] is name of the class you want updates from.
            result[class] is class object(self in a class) that you want to call when triggered
            arg keys must match the name of the parameter.
            publish a message like this: r.publish("foo", json.dumps({"bar":"argument content"})
            to publish a message, see the publish function.
        """
        name = regdata["trigger"]["class"]
        self.subscriptions.append(name)

        tmpdict = regdata
        self.funcdict[name] = tmpdict

        self.triggerdict[name] = regdata["trigger"]
        self.logger(f"subscribed to: {self.subscriptions}")
        self.listenstop = True

        self.startlisten()

    def publish(self, classinstance, data):
        """
            Allows every class to publish without importing redis.
            Usage: Watcher().publish(Foo() / "Foo", {"bar": "argumentcontent"}
            Note: using the class so that you can pass "self" from within the module.
                if using a string, that string must equal the name of the class of the result you registered earlier
        """
        if type(classinstance) != str:
            name = classinstance.__class__.__name__
        else:
            name = classinstance
        #self.logger(name)
        if type(data) == dict:
            data = json.dumps(data)
        self.r.publish(name, data)
        self.logger(f"published: {name}")

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


