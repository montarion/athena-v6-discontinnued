from components.logger import Logger

import psutil, os, json, subprocess
from datetime import timedelta
from time import time

class Monitor:
    def __init__(self, Database=None):
        self.dependencies = {"tier":"user", "dependencies":["Database"]}
        self.capabilities = []
        self.timing = {"unit": "minutes", "count":10}
        self.db = Database
        # do not add init stuff

    def checkstorage(self, drive="total"):
        # available storage left + usage in percentage
        disks = psutil.disk_partitions()
        res = {}

        for disk in disks:
            res[disk.mountpoint] = {
                "disk_free": str(psutil.disk_usage(disk.mountpoint).free),
                "disk_used": str(psutil.disk_usage(disk.mountpoint).percent),
                "disk_total": str(psutil.disk_usage(disk.mountpoint).total)
            }
        return res

    def checkmemory(self):
        res = {
            "memory_free": str(psutil.virtual_memory().percent),
            "memory_available": str(psutil.virtual_memory().available),
            "memory_total": str(psutil.virtual_memory().total)
        }
        return res

    def checknetwork(self, type="inet4"):
        netstats = psutil.net_connections(type)
        res = {"count":len(netstats)}
        return res

    def getmisc(self):
        # uptime, ?
        res = {}
        res["uptime"] = subprocess.check_output(["uptime", "-p"]).decode()[3:-1] #timedelta(seconds=time()-psutil.boot_time())
        # temp
        #res["temperature"] = psutil.sensors_temperatures()
        return res

    def compose(self):
        # get preferences from database
        res = {}
        res["storage"] = self.checkstorage()
        res["memory"] = self.checkmemory()
        #res["network"] = self.checknetwork()
        res["misc"] = self.getmisc()
        self.db.write("info", res, "monitor")

    def query(self, query, connectionID = 666):
        """connectionID is the id of who is asking(starts at 0, database is 999)
           the query is a dict containing the following keys:
            "category", "type", "data", "metadata"
        """
        category = query["category"]
        qtype = query["type"]
        data = query.get("data", None)
        metadata = query.get("metadata", None)
        response = {}
        curdict = self.db.query("info", "monitor")
        if curdict["status"][:2] == "20":
            data = curdict["resource"]
            response = self.db.messagebuilder("monitor", "info", data, metadata)

        # TODO: Read out the query
        # TODO: Use it to write out the response
        return response


    def startrun(self):
        """get system stats"""
        # init stuff..
        self.logger = Logger("Monitor").logger
        self.datapath = f"data/modules/{self.__class__.__name__.lower()}"
        self.compose()

