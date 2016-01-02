#!/usr/bin/python
"""


"""
import sys, datetime, cyclone.web, time
from twisted.internet import reactor
#from dateutil.tz import tzlocal
#from dateutil.relativedelta import relativedelta, FR
from rdflib import Namespace, Literal
from stategraph import StateGraph
sys.path.append("/my/proj/homeauto/lib")
from cycloneerr import PrettyErrorHandler
from logsetup import log, enableTwistedLog

ROOM = Namespace("http://projects.bigasterisk.com/room/")
DEV = Namespace("http://projects.bigasterisk.com/device/")

class Index(cyclone.web.RequestHandler):
    def get(self):
        self.set_header('Content-type', 'text/html')
        body = open('build/index.html').read()
        body = body.replace('SERVE_TIME', datetime.datetime.now().isoformat())
        body = body.replace('TIMESTAMP', str(time.time()))
        self.write(body)


class Application(cyclone.web.Application):
    def __init__(self):
        handlers = [
            (r"/", Index),
            (r"/(sw-import\.js)", cyclone.web.StaticFileHandler, {"path": "./"}),
            (r"/((?:components/)?[a-zA-Z0-9-]+\.(?:png|js|css|html))", cyclone.web.StaticFileHandler, {"path": "./build/"}),
        ]
        cyclone.web.Application.__init__(self, handlers)

if __name__ == '__main__':
    enableTwistedLog()
    reactor.listenTCP(8010, Application())
    reactor.run()
