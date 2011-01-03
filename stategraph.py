import datetime, os, inspect
from dateutil.tz import tzlocal
from rdflib.Graph import Graph
from rdflib import Namespace, Literal
DCTERMS = Namespace("http://purl.org/dc/terms/")

class StateGraph(object):
    """
    helper to create a graph with some of the current state of the world
    """
    def __init__(self, ctx):
        """
        note that we put the time of the __init__ call into the graph
        as its dcterms:modified time.
        """
        self.g = Graph()
        self.ctx = ctx

        requestingFile = inspect.stack()[1][1]
        self.g.add((ctx, DCTERMS['creator'], 
                    Literal(os.path.abspath(requestingFile))))
        self.g.add((ctx, DCTERMS['modified'],
               Literal(datetime.datetime.now(tzlocal()))))

    def add(self, *args, **kw):
        self.g.add(*args, **kw)

    def asTrig(self):
        return "%s {\n%s\n}\n" % (self.ctx.n3(), self.g.serialize(format='nt'))
