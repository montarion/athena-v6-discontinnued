# core file that always runs. starts networking and module discovery
import threading, os, importlib, sys
from components.database import Database as database
from components.networking import Networking as nw
from components.tasks import Tasks
from components.logger import Logger
from components.watcher import Watcher as watcher
from components.helper import Helper
from time import sleep

#test
Networking = ""
Watcher = ""
class Core:
    def __init__(self):
        self.moduledict = {}
        #self.tasker = Tasks()
        self.logger = Logger("Core").logger
        self.classobjdict = {}
        self.thismod = sys.modules[__name__] # to share networking

    def discovermodules(self):
        # find modules
        base = os.getcwd()
        os.chdir("modules")
        filelist = os.listdir()
        os.chdir(base)
        rmlist = ["__pycache__", "template.py", "output.txt", "PLAN"]
        for item in rmlist:
            if item in filelist:
                filelist.remove(item)
        tmplist = []
        for item in filelist:
            if item.split(".")[-1] == "py":
                tmplist.append(item)
        filelist = tmplist

        # import them
        
        for file in filelist:
            mod = importlib.import_module(f"modules.{file.split('.')[0]}")

            # read task data from them 
            name = file.split(".")[0].capitalize()
            
            # lets you access whatever is inside the class
            classobj = getattr(mod, name)
            # list
            attrlist = dir(classobj())
            #print(f"attrlist: {attrlist}")
           
            # actually access it.
            #dependencies = getattr(classobj, "dependencies")

            cleanlist = []
            for item in attrlist:
                if "__" not in item:
                    cleanlist.append(item)

            attrdict = {}
            for val in cleanlist:
                tmp = getattr(classobj(), val)
                if type(tmp) == list or type(tmp) == dict:
                    attrdict[val] = tmp

            #print(attrdict)
            self.moduledict[name] = {"attr":attrdict, "classobj":classobj}

        # check dependencies
        removelist = []
        tiereddepdict = {"user":{}, "preload":{}, "postuser":{}, "standalone":{}}
        #self.logger(list(self.moduledict), "debug", "yellow")
        for item in self.moduledict:    
            #self.logger(item, "debug", "blue")
            self.classobjdict[item] = self.moduledict[item]["classobj"]
            tier = self.moduledict[item]["attr"]["dependencies"]["tier"]
            # TODO: use tier to seperate dependency loading into tiers, to mitigate intermodule dependency errors
            #self.logger(self.moduledict[item])
            dependencies = self.moduledict[item]["attr"]["dependencies"]["dependencies"]
            capabilities = self.moduledict[item]["attr"]["capabilities"]
            #self.logger(f"DEPENDENCIES: {dependencies}")
            coremodules = ["Networking", "Database", "Watcher", "Helper"]
            failedlist = [x for x in dependencies if x not in coremodules and x not in list(self.moduledict.keys())]
            if len(failedlist) > 0: # TODO: if failelist includes agents, pass through anyway
                self.logger(f"couldn't meet dependencies for {item}", "info", "red")
                removelist.append(item)
        for t in removelist:
            del self.moduledict[t]
            del self.classobjdict[t]

        self.logger(f"Running modules: {list(self.moduledict)}")
        self.logger("Discovery finished.")


    def findmodulesperui(self, uidict):
        mlist = set(list(self.moduledict))  ^ (uidict.keys())
        tmpuidict = {}
        for mod in mlist:
            base = f"data/modules/{mod.lower()}/ui/"
            try:
                for name in os.listdir(base):
                    if name not in tmpuidict:
                        tmpuidict[name] = []
                    path = os.path.isdir(base + "/" + name)
                    if path:
                        tmpuidict[name].append(mod)
            except Exception as e:
                pass
        return tmpuidict

    def ontaskcomplete(self, event):
        """ returns function result on completion of scheduled task"""
        retval = event.retval
        if retval:
            id = event.job_id
            try:
                classname, funcname = self.tasker.getjobname(id)
                self.watcher.publish(classname, retval)
            except:
                pass

    def standard(self):
        global Networking, Watcher, Database
        # init database
        self.db = database()
        Database = self.db

        # start networking
        Networking = nw(self.db)
        t1 = threading.Thread(target=Networking.startserving)
        t1.start()

        # init tasker
        self.tasker = Tasks(self.db)

        # init helper
        self.helper = Helper()

        # test
        self.discovermodules()


        # start intermodule comms service
        # add core modules
        self.classobjdict["Networking"] = Networking
        self.classobjdict["Database"] = self.db
        self.classobjdict["Tasks"] = self.tasker
        self.classobjdict["Helper"] = self.helper

        #self.logger(self.classobjdict, "alert", "blue")
        Watcher = watcher(self.db, self.classobjdict)
        self.watcher = Watcher
        # add watcher to membase
        self.classobjdict["Watcher"] = Watcher

        # save it
        self.db.membase["classes"] = self.classobjdict

        # discover modules
        #self.discovermodules()
        
        # start tasks
        uiinterfaces = {}
        taskdict = {}
        for module in self.moduledict:
            name = module
            dependencies = {str(x):getattr(self.thismod, str(x)) for x in self.moduledict[module]["attr"]["dependencies"]["dependencies"]}
            #self.logger(f"Dependencies: {dependencies}", "debug", "blue")
            capabilities = self.moduledict[module]["attr"]["capabilities"]
            classobj = self.moduledict[module]["classobj"]
            task = ""
            finalclassobj = classobj(**dependencies)
            if "ui" in capabilities:
                #finalclassobj = classobj(**dependencies)
                uiinterfaces[module]= {"class": finalclassobj}
            if "blocking" in capabilities:
                # use threaded
                #finalclassobj = classobj(**dependencies)
                taskobj = getattr(finalclassobj, "startrun") # running the actual function
                task = self.tasker.createthreadedtask(taskobj) #changed from createthreadedtask
                taskdict[module] = {}
                taskdict[module]["taskobj"] = taskobj
                taskdict[module]["type"] = "threaded"
            else:
                timing = self.moduledict[module]["attr"]["timing"]
                #finalclassobj = classobj(**dependencies)
                taskobj = getattr(finalclassobj, "startrun") # running the actual function
                task = self.tasker.createtask(taskobj, timing["count"], timing["unit"], tag=module)
                taskdict[module] = {}
                taskdict[module]["task"] = task
                taskdict[module]["taskobj"] = taskobj
                taskdict[module]["timing"] = timing
            #self.logger(f"Taskdict: {taskdict}", "debug", "blue")
            # save initialized class object
            self.classobjdict[name] = finalclassobj

        self.db.membase["classes"] = self.classobjdict
        uiinterfaces = self.findmodulesperui(uiinterfaces)
        self.logger(uiinterfaces)
        self.db.membase["ui-interfaces"] = uiinterfaces
        self.db.membase["taskdict"] = taskdict
        self.tasker.addlistener(self.ontaskcomplete)
        self.logger("running!", "debug", "red")
        self.tasker.run()
