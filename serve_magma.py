#!/usr/bin/python
"""


"""
import sys, datetime, cyclone.web
from twisted.internet import reactor
#from dateutil.tz import tzlocal
#from dateutil.relativedelta import relativedelta, FR
from rdflib import Namespace, Literal
from stategraph import StateGraph
sys.path.append("/my/proj/homeauto/lib")
from cycloneerr import PrettyErrorHandler

ROOM = Namespace("http://projects.bigasterisk.com/room/")
DEV = Namespace("http://projects.bigasterisk.com/device/")

class Application(cyclone.web.Application):
    def __init__(self):
        handlers = [
            (r"/()", cyclone.web.StaticFileHandler, {"path": "build/", "default_filename": "index.html"}),
            (r"/(sw-import\.js)", cyclone.web.StaticFileHandler, {"path": "./"}),
            (r"/(icon-90\.png)", cyclone.web.StaticFileHandler, {"path": "./"}),
        ]
        cyclone.web.Application.__init__(self, handlers)

if __name__ == '__main__':
    
    reactor.listenTCP(8010, Application())
    reactor.run()
