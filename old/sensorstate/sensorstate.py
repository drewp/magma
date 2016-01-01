#!/usr/bin/python

"""
display all the RDF state data from other services
"""
import sys, os, datetime, cyclone.web, simplejson, logging, cgi, time
sys.path.extend(["../f/FuXi-1.2.production/build/lib.linux-x86_64-2.6",
                 "/my/proj/room/fuxi/build/lib.linux-x86_64-2.6/"])
from twisted.internet import reactor, defer
from twisted.web.client import getPage
from twisted.python import log
from rdflib.Graph import ConjunctiveGraph
from rdflib import Namespace, Literal, URIRef, RDFS, RDF
sys.path.extend(["/my/proj/homeauto/service/reasoning"])
from inference import parseTrig
sys.path.extend(["../../ffg/ffg", '/my/proj/ffg/ffg'])
from evtiming import logTime
from web.contrib.template import render_genshi

logging.basicConfig(level=logging.DEBUG)
render = render_genshi(os.path.dirname(__file__), auto_reload=True)

DEV = Namespace("http://projects.bigasterisk.com/device/")
ROOM = Namespace("http://projects.bigasterisk.com/room/")
CL = Namespace("http://bigasterisk.com/ns/command/v1#")

def linked(txt, uri):
    if not txt:
        txt = uri
    ret = cgi.escape(txt)
    if uri:
        ret = '<a href="%s">%s</a>' % (cgi.escape(uri), ret)
    return ret

def readGraphs():
    g = ConjunctiveGraph()
    # this file should only be reread when it changes
    g.parse("../config.n3", format="n3")
    dl = []
    startTime = time.time()
    for uri in [
        "http://bang:9055/graph",
        "http://bang:9069/graph",
        "http://bang:9070/graph",
        "http://bang:9072/bang-9002/processStatus",
        "http://bang:9072/bang/processStatus",
        "http://bang:9072/dash/processStatus",
        "http://bang:9072/slash-11000/processStatus",
        "http://bang:9072/slash/processStatus",
        "http://bang:9072/star/processStatus",
        "http://bang:9075/graph",
        ]:
        # this ought to not reparse the ones that are 304 not modified
        d = getPage(uri)
        def done(trig, uri):
            g.addN(parseTrig(trig))
            print "%s done in %.02fms" % (uri, 1000 * (time.time() - startTime))
        d.addCallback(done, uri)
        dl.append(d)
    return defer.DeferredList(dl).addCallback(lambda result: g)

class Index(cyclone.web.RequestHandler):

    def queryInputs(self, graph):
        for subclass in graph.subjects(RDFS.subClassOf, CL.Input):
            subclassLabel = graph.label(subclass)
            for sensor in graph.subjects(RDF.type, subclass):
                label = graph.label(sensor)
                yield subclass, subclassLabel, sensor, label

    def queryInputsBroken(self, graph):
        # this one is returning too much
        graph.query("""
          SELECT DISTINCT ?subclass ?subclassLabel ?sensor ?label WHERE {
            ?subclass rdfs:subClassOf cl:Input .
            # could hand-code a few more levels deep of subclasses
            OPTIONAL { ?subclass rdfs:label ?subclassLabel }
            ?sensor rdf:type ?subclass .
            OPTIONAL { ?sensor rdfs:label ?label }
          }""", initNs=dict(cl=CL, rdfs=RDFS.RDFSNS, rdf=RDF.RDFNS))

    @defer.inlineCallbacks
    def get(self):
        g = yield readGraphs()
        sections = {} # (label, sensor class) : [(label, sensor, desc), ...]
        for subclass, subclassLabel, sensor, label in self.queryInputs(g):
            sections.setdefault((subclassLabel, subclass), []
                                ).append((label, sensor,
                                          self.describeSensor(g, sensor)))

        self.set_header('Content-type', 'application/xhtml+xml')
        self.write(render.index(graph=g, sections=sections))

    def describeSensor(self, graph, uri):
        """
        xhtml describing the current state of this sensor. If I add
        live refreshes, this is the part to call again
        """
        ret = []
        for p, o in graph.query("SELECT ?p ?o WHERE { ?uri ?p ?o }",
                               initBindings=dict(uri=uri)):
            if p in [RDFS.label, RDF.type]:
                continue
            ret.append('%s: <span class="value">%s</span>' % (
                linked(graph.label(p), p),
                linked(graph.label(o), o) if isinstance(o, URIRef) else
                cgi.escape(o)))
        return '; '.join(ret)

class Application(cyclone.web.Application):
    def __init__(self):
        handlers = [
            (r"/", Index),
        ]
        cyclone.web.Application.__init__(self, handlers)

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    reactor.listenTCP(9074, Application())
    reactor.run()
