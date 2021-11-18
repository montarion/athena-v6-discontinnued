# core file that always runs. starts networking, website and module discovery
import threading, os, importlib, sys
from components.database import Database as database
from components.networking import Networking as nw
from components.tasks import Tasks
from components.logger import Logger
from components.watcher import Watcher as watcher
from components.helper import Helper
from components.oauth import Oauth as oauth
from components.security import Security as sc
from time import sleep
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

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

        self.coremodules = []
        self.taskdict = {}
        self.uiinterfaces = {}

    def filewatcher(self):
        """to (re)load new/modified files without a server restart"""
        evhandler = PatternMatchingEventHandler(["*.py"], None, False, False)

        def on_modified(event):
            self.logger(f"File {event.src_path} has been modified.")
            # get the object from self.db.membase[classes][name](has classobject, taskobject, dependencies, timing, etc). simply remove task and restart with new classobject.
            #TODO: change the discovery process so that the functions(discovermodules and the one you'll break out from standard()) can take an argument that specifies which file should be scanned. no argument means all
            simplefname = event.src_path.split("/")[-1]
            classname = simplefname.split(".")[0].capitalize()
            self.logger(f"Reloading {simplefname.capitalize()}")
            self.importfile(simplefname, True)

            # get old task data
            oldtaskobj = self.taskdict[classname]["taskobj"]
            # reload task data
            self.starttask(classname, modify = True) # will also take care of closing the old job

            # update classdict
            self.db.membase["classes"] = self.classobjdict
            self.logger(f"Reloading {classname} is finished")

        def on_created(event):
            self.logger(f"File {event.src_path} has been created.")

        evhandler.on_created = on_created
        evhandler.on_modified = on_modified
        observer = Observer()
        observer.schedule(evhandler, "modules", recursive=True)
        observer.start()

        try:
            while True:
                sleep(5)
        finally:
            observer.stop()
            observer.join()

    def importfile(self, file, reload = False):
        self.logger(f"Discover: importing {file}", "debug", "blue")
        name = file.split(".")[0].capitalize()
        if not reload:
            mod = importlib.import_module(f"modules.{file.split('.')[0]}")
        else:
            oldmod = self.moduledict[name]["module"]
            mod = importlib.reload(oldmod)
        # read task data from them

        # lets you access whatever is inside the class
        classobj = getattr(mod, name)
        # list
        attrlist = dir(classobj())

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
        self.moduledict[name] = {"attr":attrdict, "classobj":classobj, "module":mod}
        if self.insertdependencies(name):
            return True

    def insertdependencies(self, item):
        self.classobjdict[item] = self.moduledict[item]["classobj"]
        tier = self.moduledict[item]["attr"]["dependencies"]["tier"]
        # TODO: use tier to seperate dependency loading into tiers, to mitigate intermodule dependency errors
        #self.logger(self.moduledict[item])
        dependencies = self.moduledict[item]["attr"]["dependencies"]["dependencies"]
        characteristics = self.moduledict[item]["attr"]["characteristics"]
        self.logger(f"DEPENDENCIES: {dependencies}", "debug")
        failedlist = [x for x in dependencies if x not in self.coremodules and x not in list(self.moduledict.keys())]
        if len(failedlist) > 0: # TODO: if failelist includes agents, pass through anyway
            self.logger(f"couldn't meet dependencies for {item}", "info", "red")
            del self.moduledict[t]
            del self.classobjdict[t]
            return False
        return True

    def discovermodules(self):
        # find modules
        base = os.getcwd()
        os.chdir("modules")
        filelist = os.listdir()
        os.chdir(base)

        self.coremodules = [x.capitalize().split(".")[0] for x in os.listdir("components") if x.endswith(".py")]

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
            self.importfile(file)
            """ old
            self.logger(f"Discover: working on {file}", "debug")
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
            self.logger(f"Discover: Imported {name} as {self.moduledict[name]}", "debug")
            """

        """ old pt 2
        coremodules = [x.capitalize().split(".")[0] for x in os.listdir("components") if x.endswith(".py")]
        self.logger(f"coremodules: {coremodules}")
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
            characteristics = self.moduledict[item]["attr"]["characteristics"]
            self.logger(f"DEPENDENCIES: {dependencies}")
            failedlist = [x for x in dependencies if x not in coremodules and x not in list(self.moduledict.keys())]
            if len(failedlist) > 0: # TODO: if failelist includes agents, pass through anyway
                self.logger(f"couldn't meet dependencies for {item}", "info", "red")
                removelist.append(item)
        for t in removelist:
            del self.moduledict[t]
            del self.classobjdict[t]
        """
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
        jobname = self.tasker.getjobname(event.job_id)
        if "retval" in dir(event) and event.retval is not None:
            retval = event.retval
            self.logger(f"retval: {retval}", "debug", "yellow")
            id = event.job_id
            try:
                classname, funcname = self.tasker.getjobname(id)
                self.watcher.publish(classname, retval)
            except:
                pass

    def starttask(self, module, modify=False):
        name = module
        #self.logger(f"Scheduling module: {name}", "debug")
        dependencies = {str(x):getattr(self.thismod, str(x)) for x in self.moduledict[module]["attr"]["dependencies"]["dependencies"]}
        #self.logger(f"Dependencies: {dependencies}", "debug", "blue")
        characteristics = self.moduledict[module]["attr"]["characteristics"]
        capabilities = self.moduledict[module]["attr"]["capabilities"]
        classobj = self.moduledict[module]["classobj"]
        task = None
        finalclassobj = classobj(**dependencies)
        if "ui" in capabilities:
            #finalclassobj = classobj(**dependencies)
            self.uiinterfaces[module]= {"class": finalclassobj}
        if "blocking" in characteristics:
            #self.logger("scheduling module as threaded.")
            # use threaded
            #finalclassobj = classobj(**dependencies)
            taskobj = getattr(finalclassobj, "startrun") # running the actual function
            if not modify: # actually schedule the task
                task = self.tasker.createthreadedtask(taskobj) #changed from createthreadedtask
            else: # since you can't edit threads
                # close old task
                self.taskdict[module]["taskobj"].stop()
                # then start new one
                task = self.tasker.createthreadedtask(taskobj)
            self.taskdict[module] = {}
            self.taskdict[module]["taskobj"] = taskobj
            self.taskdict[module]["type"] = "threaded"
        elif "standalone"  in characteristics:
            self.taskdict[module] = {}
            self.taskdict[module]["obj"] = finalclassobj
            self.taskdict[module]["type"] = "standalone"
        else:
            timing = self.moduledict[module]["attr"]["timing"]
            #finalclassobj = classobj(**dependencies)
            taskobj = getattr(finalclassobj, "startrun") # running the actual function
            if not modify:
                task = self.tasker.createtask(taskobj, timing["count"], timing["unit"], tag=module)
            else:
                oldtask = self.tasker.removetask(self.taskdict[module]["task"])
                task = self.tasker.createtask(taskobj, timing["count"], timing["unit"], tag=module)
            self.taskdict[module] = {}
            self.taskdict[module]["task"] = task
            self.taskdict[module]["taskobj"] = taskobj
            self.taskdict[module]["timing"] = timing

        # update tasklist
        self.db.membase["taskdict"] = self.taskdict

        # update classes
        self.classobjdict[name] = finalclassobj
        self.db.membase["classes"] = self.classobjdict

        # update ui interfaces
        uiinterfaces = self.findmodulesperui(self.uiinterfaces)
        self.db.membase["ui-interfaces"] = {}
        self.db.membase["ui-interfaces"]["support"] = self.uiinterfaces

    def standard(self):
        global Networking, Watcher, Database, Oauth, Security # to fix naming conflicts when these are dependencies
        self.logger("Initializing modules")
        # init database
        self.logger("Database")
        self.db = database()
        Database = self.db

        # prepare networking
        self.logger("Prepare networking")
        Networking = nw(self.db)

        # init tasker
        self.logger("Tasker")
        self.tasker = Tasks(self.db)
        # init helper
        self.logger("Helper")
        self.helper = Helper()

        # init Oauth
        self.logger("Oauth")
        self.oauth = oauth(self.db)
        Oauth = self.oauth
        self.logger("Done.")

        #init Security:
        self.logger("Security")
        self.security = sc(self.db)
        Security = self.security
        self.logger("Done.")

        # test
        self.logger("Getting modules")
        self.discovermodules()
        self.logger("Done.")

        # no need to start website, apache does that for us

        # start intermodule comms service
        # add core modules
        self.logger("Adding core components")
        self.classobjdict["Networking"] = Networking
        self.classobjdict["Database"] = self.db
        self.classobjdict["Tasks"] = self.tasker
        self.classobjdict["Helper"] = self.helper
        self.classobjdict["Oauth"] = self.oauth
        self.classobjdict["Security"] = self.security

        #self.logger(self.classobjdict, "alert", "blue")
        Watcher = watcher(self.db, self.classobjdict)
        self.logger("Done.")
        self.watcher = Watcher
        # add watcher to membase
        self.classobjdict["Watcher"] = Watcher

        # save it
        self.db.membase["classes"] = self.classobjdict

        # start networking
        self.logger("Start networking")
        t1 = threading.Thread(target=Networking.startserving)
        t1.start()

        # start tasks
        self.uiinterfaces = {}
        self.taskdict = {}
        for module in self.moduledict:
            self.starttask(module)
            """
            name = module
            #self.logger(f"Scheduling module: {name}", "debug")
            dependencies = {str(x):getattr(self.thismod, str(x)) for x in self.moduledict[module]["attr"]["dependencies"]["dependencies"]}
            #self.logger(f"Dependencies: {dependencies}", "debug", "blue")
            characteristics = self.moduledict[module]["attr"]["characteristics"]
            capabilities = self.moduledict[module]["attr"]["capabilities"]
            classobj = self.moduledict[module]["classobj"]
            task = ""
            finalclassobj = classobj(**dependencies)
            if "ui" in capabilities:
                #finalclassobj = classobj(**dependencies)
                uiinterfaces[module]= {"class": finalclassobj}
            if "blocking" in characteristics:
                #self.logger("scheduling module as threaded.")
                # use threaded
                #finalclassobj = classobj(**dependencies)
                taskobj = getattr(finalclassobj, "startrun") # running the actual function
                task = self.tasker.createthreadedtask(taskobj) #changed from createthreadedtask
                taskdict[module] = {}
                taskdict[module]["taskobj"] = taskobj
                taskdict[module]["type"] = "threaded"
            elif "standalone"  in characteristics:
                taskdict[module] = {}
                taskdict[module]["obj"] = finalclassobj
                taskdict[module]["type"] = "standalone"
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
            #self.logger(f"Done with {name}")
            """

        #self.db.membase["classes"] = self.classobjdict # done
        #uiinterfaces = self.findmodulesperui(self.uiinterfaces)
        #self.logger(f"Supported ui interfaces: {self.uiinterfaces}", "debug")
        #self.db.membase["ui-interfaces"] = {}
        #self.db.membase["ui-interfaces"]["support"] = self.uiinterfaces
        
        #self.db.membase["taskdict"] = self.taskdict
        self.logger("Adding onTaskCompleteListener.")
        self.tasker.addlistener(self.ontaskcomplete)
        self.logger("running!", "debug", "red")
        self.tasker.run()

        # starting filewatch
        self.filewatcher()
