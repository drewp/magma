"""
where's the Command object? Lots of times these are passed to js, so
maybe the Command class will be made there. But also, usually it's
just the command uri that you need, and that's a regular rdf resource.
"""
import sys, urllib
from rdflib import URIRef, RDF, Namespace, Variable

sys.path.append('/usr/lib/python%s/site-packages/oldxml/_xmlplus/utils' %
                sys.version[:3])
import iso8601

DCTERMS = Namespace("http://purl.org/dc/terms/")
CL = Namespace("http://bigasterisk.com/ns/command/v1#")
NS = dict(cl=CL, dcterms=DCTERMS)

class CommandLog(object):
    """
    programs can call these methods to query the log, but they can
    also listen to dispatcher events. The sender will be the string
    'commandinference.db':

        signal 'commandAdded' - every command, args are uri, time, user

        ..more signals for more specific events, so listeners can filter
        better. Things like the tuple ('commandAdded', 'someType')

    There's a lot of (cmd, time, user) in here. Maybe we should be
    returning new URIs for each issued command, and you can look up
    the user in the graph yourself.    
    """
    def __init__(self, graph):
        """
        graph is an rdflib graph where we store the added commands.
        """
        self.graph = graph
        
    def addCommand(self, uri, time, user):
        """record a newly issued command

        uri is the command, which may be reused. Since we don't try to
        snapshot all the details of the command or anything, it might
        be hard to reconstruct old commands later. Commands should
        probably not be modified once they've been issued, so this uri
        stays meaningful in the future.

        time is an xs:dateTime Literal with the time the command was
        issued. Normally commands are submitted in order, but we might
        have to insert historical ones sometimes.

        user is the URI of the person who issued the command
        """
        g = self.graph
        issue = self._issueUri(uri, time, user) 
        g.add((issue, RDF.type, CL['IssuedCommand']))
        g.add((issue, CL['command'], uri))
        g.add((issue, DCTERMS['created'], time))
        g.add((issue, DCTERMS['creator'], user))
        

    def _issueUri(self, uri, time, user):
        """namespace has not been sorted out yet, and it might be
        nicer to use some other escaping (or even hashing) function on
        the other URIs."""
        secs = iso8601.parse(str(time))        
        return URIRef("http://bigasterisk.com/command/%s/%s/%s" %
                       (urllib.quote(uri), secs, urllib.quote(user)))

    def lastCommandOfClass(self, class_):
        """
        the most recent (command, time, user) entry where the command
        has the given rdf:type
        """
        for c, t, u in self.graph.query("""
                SELECT ?c ?t ?u WHERE {
                  ?issue a cl:IssuedCommand;
                         cl:command ?c .
                  ?c a ?cls .
                  ?issue dcterms:created ?t;
                         dcterms:creator ?u .
                } ORDER BY DESC(?t) LIMIT 1""",
                         initNs=NS, initBindings={Variable("?cls") : class_}):
            return c, t, u
        
    def recentCommands(self, n=10):
        """
        sequence of N recent (command, time, user) tuples. These are the
        most recent by time, not necessarily by the order that we
        learned them. The result order is from newest to oldest.

        Why does this take a limit argument AND return an iterator?
        That seems redundant.
        """
        for c, t, u in self.graph.query("""
              SELECT ?c ?t ?u WHERE {
                ?issue a cl:IssuedCommand;
                       cl:command ?c;
                       dcterms:created ?t;
                       dcterms:creator ?u .
                       } ORDER BY DESC(?t) LIMIT %s""" % n, initNs=NS):
            yield (c, t, u)
            
        
    def __len__(self):
        issues = self.graph.subjects(RDF.type, CL['IssuedCommand'])
        # this should be fixed in rdflib- iterators can have len,
        # which could easily be cheaper to compute
        return len(list(issues)) 
