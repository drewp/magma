#!buildout_bin/py
"""
adaptively pick and rank available commands according to the current
state of the world
"""
import sys
from twisted.internet.defer import inlineCallbacks, returnValue, DeferredList
from twisted.python import log
from twisted.internet import reactor
import cyclone.web
from cyclone.httpclient import fetch
import time, genshi.template, jsonlib
from rdflib.Graph import Graph, ConjunctiveGraph
from rdflib import Namespace, RDF, URIRef

sys.path.append("/my/proj/sparqlhttp")
from sparqlhttp.graph2 import SyncGraph

sys.path.append("/my/proj/room/fuxi/build/lib.linux-x86_64-2.6")
from FuXi.Rete.RuleStore import N3RuleStore

sys.path.append("/my/proj/homeauto/lib")
from cycloneerr import PrettyErrorHandler

sys.path.append("/my/proj/room")
from inference import parseTrig, infer
from commandinference.db import NS

CL = Namespace("http://bigasterisk.com/ns/command/v1#")
ROOM = Namespace("http://projects.bigasterisk.com/room/")
loader = genshi.template.TemplateLoader(".", auto_reload=True)

class PickCommands(object):
    def __init__(self, graph, user):
        self.graph, self.user = graph, user

    def makeRuleGraph(self):
        self.ruleStore = N3RuleStore()
        self.ruleGraph = Graph(self.ruleStore)
        self.ruleGraph.parse('commandRules.n3', format='n3') # for inference

    def standardRuleGraph(self):
        g = Graph()
        g.parse('commandRules.n3', format='n3')
        return g

    @inlineCallbacks
    def makeFactGraph(self):
        fileParsing = httpReading = 0
        g = ConjunctiveGraph()
        fileParsing -= time.time()
        g.parse("config.n3", format="n3")
        fileParsing += time.time()
        g.add((self.user, RDF.type, CL.CurrentUser))

        httpReading -= time.time()

        @inlineCallbacks
        def addData(source):
            trig = (yield fetch(source)).body
            try:
                g.addN(parseTrig(trig))
            except Exception:
                import traceback
                print "fetching %s:" % source
                traceback.print_exc()

        yield DeferredList(map(addData,
            ["http://bang:9072/bang/processStatus",
            "http://bang:9055/graph", # heater, etc
            "http://bang:9069/graph", # door/arduino inputs
            "http://bang:9070/graph", # wifi
            "http://bang:9075/graph", # env
             ]))

        httpReading += time.time()
        self.factGraph = g
        returnValue((fileParsing, httpReading))
    
    @inlineCallbacks
    def run(self):
        """
        list of (command uris, rank) with most relevant first
        """
        fileParsing = 0
        httpReading = 0

        fileParsing -= time.time()
        self.makeRuleGraph()
        fileParsing += time.time()

        (f2, h2) = yield self.makeFactGraph()
        fileParsing += f2
        httpReading += h2

        self.target = infer(self.factGraph, self.ruleStore)

        rankCmd = {}
        for cmd, rank in self.target.query("SELECT DISTINCT ?cmd ?rank WHERE { ?cmd a cl:available . OPTIONAL { ?cmd cl:ranking ?rank } }", initNs=dict(cl=CL)):
            rankCmd[cmd] = rankCmd.get(cmd, 0) + float(rank or 0)

        ret = sorted(rankCmd.items(), key=lambda (cmd,r): (r, cmd),
                     reverse=True)

        self.timeReport = (
            "spent %.1fms parsing files, %.1fms fetching http" % (
                1000 * fileParsing, 1000 * httpReading))

        returnValue(ret)

def user(req):
    return URIRef(req.headers['X-Foaf-Agent'])

class Index(PrettyErrorHandler, cyclone.web.RequestHandler):
    @inlineCallbacks
    def get(self):
        pc = PickCommands(self.settings.graph, user(self.request))
        d = yield pc.run()
        def altSerialize(g):
            return (g.serialize(format='n3')
                    .replace(';\n     ', '; ')
                    .replace(',\n     ', ', ')
                    .replace("\n\n", "\n"))
        data = dict(cmds=d, pc=pc, altSerialize=altSerialize)
        self.set_header("Content-Type", "application/xhtml+xml")
        self.write(loader.load("dyncommands.html").generate(**data).render('xhtml'))

class Commands(PrettyErrorHandler, cyclone.web.RequestHandler):
    def get(self):
        pc = PickCommands(self.settings.graph, user(self.request))
        d = pc.run()
        d.addCallback(lambda cmds: self.write(jsonlib.dumps(cmds)))
        return d
    
if __name__ == '__main__':
    graph = SyncGraph("sesame",
                      "http://bang:8080/openrdf-sesame/repositories/cmd",
                      initNs=NS)
    
    log.startLogging(sys.stdout)
    reactor.listenTCP(8007, cyclone.web.Application([
        (r"/", Index),
        (r"/commands", Commands),
        ], graph=graph))
    reactor.run()
