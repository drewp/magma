"""
for all clients of the db
"""
import sys
sys.path.append("/my/site/photo")
sys.path.append('/usr/lib/python%s/site-packages/oldxml/_xmlplus/utils' %
                sys.version[:3])
from remotesparql import RemoteSparql
from rdflib import Literal, Namespace
import iso8601, time
from db import CommandLog, NS
XS = Namespace("http://www.w3.org/2001/XMLSchema#")

def buildCommandLog(seedGraphFilename, sleepycatDir="db"):
    """load an n3 file with command definitions and initial
    conditions, plus a sleepycat db, and make a db.CommandLog
    configured to write new commands to the sleepycat graph"""
    raise NotImplementedError("use getCommandLog")
    seedGraph = ConjunctiveGraph()
    seedGraph.parse(seedGraphFilename, format='n3')

    outGraph = ConjunctiveGraph('Sleepycat')
    outGraph.open(sibpath(__file__, 'db'))
    atexit.register(lambda: outGraph.close(commit_pending_transaction=True))

    commandLog = db.CommandLog(ReadOnlyGraphAggregate([seedGraph, outGraph]),
                               writeGraph=outGraph)
    return commandLog


def getCommandLog():
    graph = RemoteSparql("http://bang:8080/openrdf-sesame/repositories", "cmd", initNs=NS)
    cl = CommandLog(graph)
    return cl

def nowLiteral():
    return Literal(iso8601.tostring(time.time(), (time.timezone, time.altzone)[time.daylight]),
                   datatype=XS['dateTime'])
