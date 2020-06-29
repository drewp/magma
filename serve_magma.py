#!/usr/bin/python
"""


"""
import datetime, cyclone.web, time
from pathlib import Path
from twisted.internet import reactor
from rdflib import Namespace
from cycloneerr import PrettyErrorHandler
from standardservice.logsetup import log

ROOM = Namespace("http://projects.bigasterisk.com/room/")
DEV = Namespace("http://projects.bigasterisk.com/device/")

class Index(PrettyErrorHandler, cyclone.web.RequestHandler):
    def get(self):
        self.set_header('Content-type', 'text/html')
        body = open('newindex.html').read()
        body = body.replace('STYLE_MTIME', 
          str(Path("./build/style.css").stat().st_mtime))
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
    reactor.listenTCP(8010, Application())
    reactor.run()
