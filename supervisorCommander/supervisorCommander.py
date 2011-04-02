#!buildout_bin/py
"""
RDF interface to supervisord. Reports existing processes and their
states as linked data. Also takes POSTed json events with similar URIs
and executes them as supervisor commands.

Talks to multiple supervisor instances. Pass them as cmdline args:
python supervisorCommander.py http://host1:9001 http://host2:9001


subscribe to 'newCommand' on the PSHB hub. When commands come for
supervisors, send them out to the appropriate servers. Also includes
reporting the status of supervisor processes in an rdf graph.
"""

import sys, cyclone.web, cyclone.httpclient, simplejson, xmlrpclib, re, cgi
from optparse import OptionParser
from twisted.python import log
from twisted.internet import reactor
from rdflib import URIRef, Literal, RDFS, RDF
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
        self.write("this is supervisorcommander, talking to supervisors at: " +
                   ", ".join('<a href="%s">%s</a>' % (cgi.escape(comp),
                                                      cgi.escape(uri))
                             for comp, uri in sorted(
                                 self.settings.addresses.items())))

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

def getConnection(conns, uri):
    if uri in conns:
        return conns[uri]
    serv = conns[uri] = xmlrpclib.ServerProxy(uri)
    return serv

class ProcessStatus(cyclone.web.RequestHandler):
    def get(self, addr):
        """run state of all processes on this supervisor"""
        serv = getConnection(self.settings.xmlrpcConnections,
                             self.settings.addresses[addr])
        infos = serv.supervisor.getAllProcessInfo()
        graph = StateGraph(ctx=CL['supervisors'])
        for p in infos:
            processUri = URIRef("http://bigasterisk.com/magma/sup/%s/%s" %
                                (addr, p['name']))
            graph.add((processUri, RDF.type,
                       URIRef("http://bigasterisk.com/ns/command/v1#Process")))
            graph.add((processUri, RDFS.label, Literal(p['name'])))
            state = URIRef('http://supervisord.org/config#%s' % p['statename'])
            graph.add((processUri, CL.state, state))
            graph.add((state, RDFS.label, Literal(p['statename'])))
            
        # return status and some log tail
        self.set_header('Content-Type', 'application/x-trig')
        self.write(graph.asTrig())

class Application(cyclone.web.Application):
    def __init__(self, args):
        handlers = [
            (r"/", Index),
            (r"/(.*?)/processStatus", ProcessStatus),
            #(r"/processStatus", CombinedProcessStatus),
            (r'/(.*?)/newCommand', NewCommandHandler),
            #(r'/graph', GraphHandler),
        ]
        settings = {
            'cmdlog': None,#getCommandLog(),
            'addresses' : self.pickAddresses(args),
            'xmlrpcConnections' : {}
            }
        cyclone.web.Application.__init__(self, handlers, **settings)

    def pickAddresses(self, args):
        """
        dict of shortname : url, where shortname is what to use in the
        url tree, and url is the xmlrpc supervisor endpoint from the
        cmdline
        """
        addresses = {}
        for arg in args:
            m = re.match("https?://(.*):", arg)
            if m and m.group(1) not in addresses:
                addresses[m.group(1)] = arg
                continue
            m = re.match("https?://(.*):(\d+)", arg)
            if m:
                comp = "%s-%s" % (m.group(1), m.group(2))
                if comp not in addresses:
                    addresses[comp] = arg
                    continue
            raise ValueError(
                "can't figure out what to url component to use for %r" % arg)
        return addresses

if __name__ == '__main__':
    parser = OptionParser(usage="%prog [urls of supervisor instances, such as http://localhost:9001]")
    opts, args = parser.parse_args()
    log.startLogging(sys.stdout)
    reactor.listenTCP(9072, Application(args))
    reactor.run()
