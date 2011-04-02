#!buildout_bin/py
"""
subscribe to 'newCommand' on the PSHB hub. When commands come for
supervisors, send them out to the appropriate servers. Also includes
reporting the status of supervisor processes in an rdf graph.
"""

import sys, cyclone.web, cyclone.httpclient, simplejson, xmlrpclib
from twisted.python import log
from twisted.internet import reactor
from rdflib import URIRef, Literal, RDFS
from commandinference.dbclient import getCommandLog
from commandinference.db import CMD, CL

from stategraph import StateGraph

def getSupervisorParams(graph, commandUri):
    rows = graph.queryd("""
    SELECT DISTINCT ?supervisor ?processLabel WHERE {
      ?cmd cl:supervisorProcess [
        cl:supervisor ?supervisor ;
        cl:processLabel ?processLabel ].
    }
    """, initBindings=dict(cmd=commandUri))
    if len(rows) != 1:
        raise ValueError("found %s matches for %r" %
                         (len(rows), commandUri))
    return rows[0]

class Index(cyclone.web.RequestHandler):
    def get(self):
        self.write("this is supervisorcommander")

class NewCommandHandler(cyclone.web.RequestHandler):
    def post(self):
        event = simplejson.loads(self.request.body)
        # remember we may get hit twice with different command
        # types. the correct way to get a single run would be to use
        # the issue uri.

        #{'issue': 'http://bi1111', 'created': '2011-02-12T22:11:53-08:00', 'command': 'http://bigasterisk.com/magma/cmd/backupPreDrew', 'commandClass': 'http://bigasterisk.com/magma/cmd/SupervisorStart', 'creator': 'http://bigasterisk.com/foaf.rdf#drewp'}

        if URIRef(event['commandClass']) not in [
            CMD['SupervisorStart'], CMD['SupervisorStop']]:
            return

        print "command", event

        graph = self.settings.cmdlog.graph
                
        params = getSupervisorParams(graph, URIRef(event['command']))
        serv = xmlrpclib.ServerProxy(params['supervisor'])
        action = {
            CMD['SupervisorStart'] : 'startProcess',
            CMD['SupervisorStop'] : 'stopProcessGroup',
            }[URIRef(event['commandClass'])]
            
        getattr(serv.supervisor, action)(unicode(params['processLabel']))
        
        self.write("done")

class ProcessStatus(cyclone.web.RequestHandler):
    def get(self):
        serv = xmlrpclib.ServerProxy('http://bang:9001')
        infos = serv.supervisor.getAllProcessInfo()
        graph = StateGraph(ctx=CL['supervisors'])
        for p in infos:
            processUri = URIRef("http://bigasterisk.com/magma/sup/bang/9001/%s" % p['name'])
            graph.add((processUri, RDFS.label, Literal(p['name'])))
            state = URIRef('http://supervisord.org/config#%s' % p['statename'])
            graph.add((processUri, CL.state, state))
            graph.add((state, RDFS.label, Literal(p['statename'])))
            
        # return status and some log tail
        self.set_header('Content-type', 'application/x-trig')
        self.write(graph.asTrig())

class Application(cyclone.web.Application):
    def __init__(self):
        handlers = [
            (r"/", Index),
            (r"/processStatus", ProcessStatus),
            (r'/newCommand', NewCommandHandler),
            #(r'/graph', GraphHandler),
        ]
        settings = {
            'cmdlog': getCommandLog(),
            }
        cyclone.web.Application.__init__(self, handlers, **settings)


if __name__ == '__main__':
    log.startLogging(sys.stdout)
    reactor.listenTCP(9072, Application())
    reactor.run()
