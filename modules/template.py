from components.logger import Logger

class Template:
    def __init__(self, Networking=None):
        self.dependencies = {"tier":"user", "dependencies":["Networking"]}
        self.capabilities = []
        self.timing = {"unit": "minutes", "count":10}
        # do not add init stuff

        def dostuff(self):
            pass

    def startrun(self):
        """Description of what this module does"""
        # init stuff..
        self.logger = Logger("Killswitch").logger
        self.datapath = f"data/modules/{self.__class__.__name__.lower()}"
        self.dostuff()
