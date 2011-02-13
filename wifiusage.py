#!/usr/bin/python
"""
scrape the tomato router status pages to see who's connected to the
wifi access points. Includes leases that aren't currently connected.

Returns:
 json listing (for magma page)
 rdf graph (for reasoning)
 activity stream, when we start saving history

Todo: this should be the one polling and writing to mongo, not entrancemusic
"""
import sys, os, datetime, cyclone.web, simplejson
from twisted.python import log
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.web.client import getPage
from dateutil.tz import tzutc, tzlocal
from pymongo import Connection
from rdflib.Graph import Graph
from rdflib import Namespace, Literal, URIRef
from stategraph import StateGraph
sys.path.append("/my/proj/entrancemusic")
from entrancemusic import routers, getPresentMacAddrs, getName

DEV = Namespace("http://projects.bigasterisk.com/device/")
ROOM = Namespace("http://projects.bigasterisk.com/room/")

class Index(cyclone.web.RequestHandler):
    def get(self):
        self.write("this is wifiusage")

        
class Json(cyclone.web.RequestHandler):
    def get(self):
        out = []
        for mac, signal, networkName in getPresentMacAddrs(routers):
            out.append(dict(mac=mac, signal=signal, networkName=networkName,
                            name=getName(mac, networkName)))
        self.write(simplejson.dumps({"wifi" : out}))
        

class GraphHandler(cyclone.web.RequestHandler):
    def get(self):
        g = StateGraph(ctx=DEV['wifi'])

        # someday i may also record specific AP and their strength,
        # for positioning. But many users just want to know that the
        # device is connected to some bigasterisk AP.
        aps = URIRef("http://bigasterisk.com/wifiAccessPoints")
        
        for mac, signal, networkName in getPresentMacAddrs(routers):
            uri = URIRef("http://bigasterisk.com/wifiDevice/%s" % mac)
            g.add((uri, ROOM['macAddress'], Literal(mac)))
            g.add((uri, ROOM['connected'], aps))
            g.add((uri, ROOM['wifiNetworkName'], Literal(networkName)))
            g.add((uri, ROOM['deviceName'], Literal(getName(mac, networkName))))
            g.add((uri, ROOM['signalStrength'], Literal(signal)))

        self.set_header('Content-type', 'application/x-trig')
        self.write(g.asTrig())
        

class Application(cyclone.web.Application):
    def __init__(self):
        handlers = [
            (r"/", Index),
            (r'/json', Json),
            (r'/graph', GraphHandler),
            #(r'/activity', Activity),
        ]
        settings = {
            'mongo' : Connection('bang', 27017,
                                 tz_aware=True)['house']['sensor']
            }
        cyclone.web.Application.__init__(self, handlers, **settings)

if __name__ == '__main__':
    #log.startLogging(sys.stdout)
    reactor.listenTCP(9070, Application())
    reactor.run()
