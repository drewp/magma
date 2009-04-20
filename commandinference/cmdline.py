"""
for cmdline clients
"""

from rdflib import URIRef
from dbclient import getCommandLog # legacy

def uriFromArg(a):
    if ':' in a and '/' not in a:
        prefix, name = a.split(':')
        full = {'cmd' : 'http://bigasterisk.com/magma/cmd/'}[prefix]
        return URIRef(full + name)
    return URIRef(a)
        
def prettyCommand((c, t, u)):
    return "%-60s %-24s  %s" % (unicode(c), unicode(t), unicode(u))
