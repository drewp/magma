"""
where's the Command object? Lots of times these are passed to js, so
maybe the Command class will be made there. But also, usually it's
just the command uri that you need, and that's a regular rdf resource.
"""
import sys, urllib
from rdflib import URIRef, RDF, Namespace, Variable, Literal, RDFS
from time import strftime

sys.path.append('/usr/lib/python%s/site-packages/oldxml/_xmlplus/utils' %
                sys.version[:3])
import iso8601

DCTERMS = Namespace("http://purl.org/dc/terms/")
CL = Namespace("http://bigasterisk.com/ns/command/v1#")
XS = Namespace("http://www.w3.org/2001/XMLSchema#")
CMD = Namespace("http://bigasterisk.com/magma/cmd/")
ROOM = Namespace("http://projects.bigasterisk.com/room/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
MB = Namespace("http://bigasterisk.com/ns/microblog/")
NS = dict(cl=CL, cmd=CMD, dcterms=DCTERMS, rdfs=RDFS.RDFSNS, foaf=FOAF, mb=MB)

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
    def __init__(self, graph, writeGraph=None):
        """
        graph is an rdflib Graph2 where we store the added commands.

        All queries are done on graph, but new triples are written to
        writeGraph, if it is provided. writeGraph should be a subset
        of graph.
        """
        self.graph = graph
        self.writeGraph = writeGraph
        if self.writeGraph is None:
            self.writeGraph = graph
        
    def addCommand(self, uri, time, user):
        """record a newly issued command. returns uri of issue

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
        assert isinstance(time, Literal)

        #if not self.graph.contains(uri, RDF.type, command
        
        g = self.writeGraph
        issue = self._issueUri(uri, time, user) 
        g.add((issue, RDF.type, CL['IssuedCommand']),
              (issue, CL['command'], uri),
              (issue, DCTERMS['created'], time),
              (issue, DCTERMS['creator'], user),
              # separate into smaller contexts for backup and sync purposes
              context=CL[strftime('commands/%Y/%m')]
              )
        g.commit()

        # ping listeners here
        return issue

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

        in sesame:
        curl -H "Accept: application/sparql-results+json" "http://bang:8080/openrdf-sesame/repositories/cmd?query=PREFIX%20cl%3A%3Chttp%3A%2F%2Fbigasterisk.com%2Fns%2Fcommand%2Fv1%23%3E%0APREFIX%20rdf%3A%3Chttp%3A%2F%2Fwww.w3.org%2F1999%2F02%2F22-rdf-syntax-ns%23%3E%0APREFIX%20dcterms%3A%3Chttp%3A%2F%2Fpurl.org%2Fdc%2Fterms%2F%3E%0APREFIX%20mc%3A%3Chttp%3A%2F%2Fbigasterisk.com%2Fmagma%2Fcmd%2F%3E%0A%0ASELECT%20%3Fc%20%3Ft%20%3Fu%20WHERE%20\{%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%3Fissue%20a%20cl%3AIssuedCommand%3B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20cl%3Acommand%20%3Fc%20.%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%3Fc%20a%20%20mc%3AHeater.%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%3Fissue%20dcterms%3Acreated%20%3Ft%3B%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20dcterms%3Acreator%20%3Fu%20.%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20\}%20ORDER%20BY%20DESC%28%3Ft%29%20LIMIT%201"

        
        """
        for row in self.graph.queryd("""
                SELECT ?c ?t ?u WHERE {
                  ?issue a cl:IssuedCommand;
                         cl:command ?c .
                  ?c a ?cls .
                  ?issue dcterms:created ?t;
                         dcterms:creator ?u .
                } ORDER BY DESC(?t) LIMIT 1""",
                         initBindings={Variable("cls") : class_}):
            return row['c'], row['t'], row['u']
        raise ValueError("No commands found of class %r" % class_)
        
    def recentCommands(self, n=10):
        """
        sequence of N recent (command, time, user) tuples. These are the
        most recent by time, not necessarily by the order that we
        learned them. The result order is from newest to oldest.

        Why does this take a limit argument AND return an iterator?
        That seems redundant.
        """
        for row in self.graph.queryd("""
              SELECT ?c ?t ?u WHERE {
                ?issue a cl:IssuedCommand;
                       cl:command ?c;
                       dcterms:created ?t;
                       dcterms:creator ?u .
                       } ORDER BY DESC(?t) LIMIT %s""" % n):
            yield (row['c'], row['t'], row['u'])
            
        
    def __len__(self):
        issues = self.graph.subjects(RDF.type, CL['IssuedCommand'])
        # this should be fixed in rdflib- iterators can have len,
        # which could easily be cheaper to compute
        return len(list(issues)) 
