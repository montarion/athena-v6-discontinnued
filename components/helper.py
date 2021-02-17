from components.logger import Logger

import os, re, json

from time import time
from datetime import timedelta

class Helper:
    """Contains helper functions like common conversions"""
    def __init__(self):
        pass

    def epochtopassed(self, epoch):
        diff = time() - epoch
        td = timedelta(seconds=diff)
        d, h, m = td.days, td.seconds//3600, (td.seconds//60)%60
        timestr = ""
        if d>1:
            timestr = "Days ago."
        if h >0 and d>0:
            timestr = f"{d} days and {h} hours ago."
        elif h>0 and d==0:
            timestr = f"{h} hours and {m} minutes ago."
        elif h==0 and d>0:
            timestr = f"{d} days ago."
        elif h==0 and d==0:
            timestr = f"{m} minutes ago."
        elif h==0 and d==0 and m==0:
            timestr = "Less than a minute ago."
        else:
            timestr = "Time is irrelevant"
        return timestr
