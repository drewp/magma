"""
for all clients of the db
"""
import sys, logging
sys.path.append("/my/proj/sparqlhttp")
from sparqlhttp.graph2 import SyncGraph
from rdflib import Literal
import time, jsonlib, restkit, datetime
from dateutil.tz import tzlocal
from commandinference.db import CommandLog, NS, XS

log = logging.getLogger()

def buildCommandLog(seedGraphFilename, sleepycatDir="db"):
    """load an n3 file with command definitions and initial
    conditions, plus a sleepycat db, and make a db.CommandLog
    configured to write new commands to the sleepycat graph"""
    raise NotImplementedError("use getCommandLog")
  


def getCommandLog():
    graph = SyncGraph("sesame",
                      "http://bang:8080/openrdf-sesame/repositories/cmd",
                      initNs=NS)
    
    cl = CommandLog(graph)
    return cl

def nowLiteral():
    return Literal(
        datetime.datetime.now(tzlocal()).isoformat(),
        datatype=XS['dateTime'])
