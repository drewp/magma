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
from rdflib import Graph, ConjunctiveGraph
from rdflib import Namespace, RDF, URIRef

# see buildout.cfg for the extra-paths that let these work
from sparqlhttp.graph2 import SyncGraph
from FuXi.Rete.RuleStore import N3RuleStore
from cycloneerr import PrettyErrorHandler
from rdflib import RDFS
RDFS.uri = RDFS.RDFSNS # compat with rdflib 2.4.2
from commandinference.db import NS, CMD

sys.path.append("/my/proj/homeauto/service/reasoning")
from inference import parseTrig, infer


CL = Namespace("http://bigasterisk.com/ns/command/v1#")
ROOM = Namespace("http://projects.bigasterisk.com/room/")
loader = genshi.template.TemplateLoader(".", auto_reload=True)

class PickCommands(object):
    def __init__(self, graph, user):
        self.graph, self.user = graph, user

    def makeRuleGraph(self):
        self.ruleStore = N3RuleStore()
        class NullDispatcher(object):
            def dispatch(self, *args):
                pass
        self.ruleStore.dispatcher = NullDispatcher()
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
            try:
                trig = (yield fetch(source)).body
            except AttributeError:
                print vars()
                raise
            try:
                g.addN(parseTrig(trig))
            except Exception:
                import traceback
                print "fetching %s:" % source
                traceback.print_exc()

        yield DeferredList(map(addData,
            # compare to reasoning and reasoning/input/startup.n3
            ["http://bang:9072/bang/processStatus",
             #"http://bang:9055/graph", # heater, etc
             #"http://bang:9069/graph", # door/arduino inputs
             "http://bang:9070/graph", # wifi
             "http://bang:9075/graph", # env
             "http://slash:9080/graph", # frontdoor
             #"http://dash:9107/graph", # xidle
             #"http://dash:9095/graph", # dpms
             #"http://bang:9095/graph", # dpms
             #"http://star:9095/graph", # dpms
             "http://slash:9095/graph", # dpms

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

class CommandsTable(PrettyErrorHandler, cyclone.web.RequestHandler):
    @inlineCallbacks
    def get(self):

        pc = PickCommands(self.settings.graph, user(self.request))
        cmds = yield pc.run()

        tops = [[]] # rows of 3
        belowZero = []

        for (cmd, score) in cmds:
            cmd = URIRef(cmd)
            if score < 0:
                belowZero.append(self._buttonData(cmd, score))
                continue
            if len(tops[-1]) >= 3:
                tops.append([])
            tops[-1].append(self._buttonData(cmd, score))

        self.write(loader.load("dyncommandstable.html").generate(tops=tops, belowZero=belowZero).render('xhtml'))

    def _buttonData(self, cmd, score):
        # note that this reads from sesame, while the cmd came from a fresh read of config.n3
        
        matches = self.settings.graph.queryd("""
     SELECT DISTINCT ?label ?icon ?linksTo WHERE {
       ?user cl:seesCommand ?uri .
       ?uri rdfs:label ?label .
       OPTIONAL { ?uri cl:buttonIcon ?icon }
       OPTIONAL { ?uri cl:linksTo ?linksTo }
     } ORDER BY ?label 
    """, initBindings={"uri" : cmd})
        if len(matches) != 1:
            raise ValueError("found %s matches for command %r" % (len(matches), cmd))
            
        row = matches[0]

        row['cmd'] = cmd
        row['score'] = score

        isLink = self.settings.graph.queryd("ASK { ?cmd a cl:CommandLink }",
                                   initBindings={"cmd" : cmd})

        if row.get('linksTo') or isLink:
            row['method'], row['action'] = "get", row['linksTo'] or cmd
            row['isLink'] = True
        else:
            row['method'], row['action'] = 'post', 'addCommand'
            row['isLink'] = False

        buttonClass = ''
        if cmd in [CMD.BabyStart, CMD.BabyStop]:
            # needs to be fixed and replaced with something any command can use to return availability status
            last, _, _ = self.cmdlog.lastCommandOfClass(CL.BabyStartStop)
            if last == cmd:
                buttonClass += " current"
            else:
                buttonClass += " recommend"
        
        return row


    def more(self):

        trs = [T.tr['']]

        response = yield fetch("http://bang:8007/commands",
                               headers={"X-Foaf-Agent":[str(self.user)]})
        if not response:
            raise ValueError('-H "X-Foaf-Agent: %s" http://bang:8007/commands failed' % str(self.user))
        cmds = jsonlib.loads(response.body)

        belowZero = []

        for (cmd, score) in cmds:
            cmd = URIRef(cmd)
            if score < 0:
                belowZero.append((cmd, score))
                continue

            if len(trs[-1].children) >= 1 + columns:
                trs.append(T.tr[''])
            trs[-1].children.append(T.td["\n", self._buttonForm(cmd, score)])

        trs.append(T.tr[T.td(colspan=columns)])
        for (cmd, score) in belowZero:
            trs[-1].children[-1][self._buttonForm(cmd, score)]
        returnValue(T.table[trs])
    
if __name__ == '__main__':
    graph = SyncGraph("sesame",
                      "http://bang:8080/openrdf-sesame/repositories/cmd",
                      initNs=NS)
    
    log.startLogging(sys.stdout)
    reactor.listenTCP(8007, cyclone.web.Application([
        (r"/", Index),
        (r"/commands", Commands),
        (r'/commands/table', CommandsTable),
        ], graph=graph))
    reactor.run()
