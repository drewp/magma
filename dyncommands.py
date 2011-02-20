"""
adaptively pick and rank available commands according to the current
state of the world
"""
from twisted.internet.defer import inlineCallbacks, returnValue
from cyclone.httpclient import fetch
import sys, time
sys.path.append("/my/proj/room/fuxi/build/lib.linux-x86_64-2.6")
from FuXi.Rete.RuleStore import N3RuleStore
from rdflib.Graph import Graph, ConjunctiveGraph
from rdflib import Namespace, RDF
sys.path.append("/my/proj/room")
from inference import parseTrig, infer
CL = Namespace("http://bigasterisk.com/ns/command/v1#")

@inlineCallbacks
def pickCommands(graph, user):
    """
    list of useful command uris with most relevant first
    """
    fileParsing = 0
    httpReading = 0

    ruleStore = N3RuleStore()
    ruleGraph = Graph(ruleStore)
    fileParsing -= time.time()
    ruleGraph.parse('commandRules.n3', format='n3') # for inference
    fileParsing += time.time()

    g = ConjunctiveGraph()
    fileParsing -= time.time()
    g.parse("config.n3", format="n3")
    fileParsing += time.time()
    g.add((user, RDF.type, CL.CurrentUser))
    # parallelize these!
    httpReading -= time.time()
    for source in ["http://bang:9072/processStatus",
                   "http://bang:9055/graph",
                   #"http://bang:9069/graph", # door/arduino inputs
                   #"http://bang:9070/graph", # wifi
                   ]:
        trig = (yield fetch(source)).body
        g.addN(parseTrig(trig))
    httpReading += time.time()
    print "facts", len(g)

    target = infer(g, ruleStore)
    for s in target:
        print "target", s

    rankCmd = {}
    for s,p,o in target.triples((None, CL.ranking, None)):
        rankCmd[s] = o
    ret = sorted(rankCmd.keys(), key=lambda cmd: (rankCmd[cmd], cmd))
    for cmd in ret:
        print "rank", cmd, rankCmd[cmd]

    print "spent %.1fms parsing files, %.1fms fetching http" % (
        1000 * fileParsing, 1000 * httpReading)
        
    returnValue(ret)
    
