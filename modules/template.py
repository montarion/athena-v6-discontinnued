from components.logger import Logger

class Template:
    def __init__(self, Networking=None):
        self.dependencies = {"tier":"user", "dependencies":["Networking"]}
        self.capabilities = []
        self.timing = {"unit": "minutes", "count":10}
        # do not add init stuff

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
        # TODO: Read out the query
        # TODO: Use it to write out the response
        return response


    def startrun(self):
        """Description of what this module does"""
        # init stuff..
        self.logger = Logger("Killswitch").logger
        self.datapath = f"data/modules/{self.__class__.__name__.lower()}"
        self.dostuff()
