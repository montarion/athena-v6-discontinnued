import os, threading


class Compression:
    def __init__(self, Database):
        self.db = Database()
        self.progport = 12753

    def getprogress(self):
        # see compression.py on GREYTITAN
        pass

    def getftpfilepath(self, localfilename):
        pass

    def compressfile(self, filepath, episode)
        if filepath.startswith("/"):
            foldername = filepath
        else:
            foldername = os.abspath(filepath)
        filename = filepath.split("/")[-1]

    # get target machine id
        nw = self.db.membase["classes"]["Networking"]
        id = nw.findtarget("compression")[0]
    # write message
        dlinfo = {"url": "192.168.178.34", "location":foldername, "name": filename, "progport": self.progport}
        upinfo = {"url": "192.168.178.34", "rlocation":foldername}
        data = {"down": dlinfo, "up": upinfo}
        message = {"category":"compute", "type":"compress", "data":data}
    # send message
        nw.regsend(message, [id])
    # start getprogress() in new thread
    
