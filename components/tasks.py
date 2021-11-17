import json, threading

import apscheduler
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger as trigger
from apscheduler import events
from time import sleep
from components.logger import Logger
from datetime import datetime


class Tasks:
    def __init__(self, Database):
        self.logger = Logger("Tasks").logger
        self.db = Database
        #self.schedule = AsyncIOScheduler() 
        self.schedule = BackgroundScheduler()
        self.threadlist = []
        self.uilist = []

    def createtask(self, functarget, count, unit, tag="user task"):
        #task = getattr(schedule.every(count), unit).do(functarget).tag(tag)
        kwargs = {unit: count}
        self.logger(f"scheduled task {functarget} to run every {count} {unit}", "debug")
        task = self.schedule.add_job(functarget, trigger(**kwargs), jitter=10, misfire_grace_time=None)
        self.logger(task, "debug")
        return task

    def createthreadedtask(self, functarget, argdict={}):
        task = threading.Thread(target=functarget, kwargs=argdict)
        #task = self.schedule.add_job(task.start)
        self.threadlist.append(task)
        return task

    def removetask(self, task):
        self.logger(f"Removing task: {task}", "debug")
        task.remove()

    def pause(self, target):
        # check if target in membase. if so, stop execution
        taskdict = self.db.membase["taskdict"]
        if target in taskdict and "task" in taskdict[target]:
            job = taskdict[target]["task"]
            job.pause()
            self.logger(f"Paused: {target}")

    def resume(self, target):
        taskdict = self.db.membase["taskdict"]
        if target in taskdict:
            job = taskdict[target]["task"]
            job.pause()
            self.logger(f"Resumed: {target}")


    def run(self):
        self.logger("running everything")
        for task in self.threadlist:
            task.start()

        self.schedule.start()

    def getjobs(self):
        self.schedule.print_jobs()
        return self.schedule.get_jobs()

    def getjobname(self, jobid=None):
        tmpjoblist = self.schedule.get_jobs()
        jobdict = {}
        for job in tmpjoblist:
            name = job.name
            job = job.id
            jobdict[job] = name

        if jobid in jobdict:
            name = jobdict[jobid]
            classname, funcname = name.split(".")
            return classname, funcname
        return 404, 404

    def addlistener(self, function):
        self.schedule.add_listener(function, mask=4096)
