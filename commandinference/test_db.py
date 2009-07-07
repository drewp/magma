from twisted.trial import unittest
from rdflib import Namespace, Literal, RDF
from rdflib.Graph import ConjunctiveGraph
from db import CommandLog
from sparqlhttp.dictquery import Graph2

CMD = Namespace("http://example.com/")
USER = Namespace("http://example.com/user/")
XS = Namespace("http://www.w3.org/2001/XMLSchema#")
DCTERMS = Namespace("http://purl.org/dc/terms/")
CL = Namespace("http://bigasterisk.com/ns/command/v1#")
INITNS = dict(cl=CL, dcterms=DCTERMS)

def dateTime(timeStr):
    return Literal("2008-12-01T%s-08:00" % timeStr, datatype=XS['dateTime'])

class WithGraph(object):
    def setUp(self):
        super(WithGraph, self).setUp()
        self.graph = ConjunctiveGraph()
        self.graph.add((CMD['c2'], RDF.type, CMD['Bright']))
        self.cl = CommandLog(Graph2(self.graph, initNs=INITNS))

class TestLogAdd(WithGraph, unittest.TestCase):
    def testNormalAdd(self):
        self.assertEqual(len(self.cl), 0)
        self.cl.addCommand(CMD['c1'], dateTime('18:00:00'), USER['drewp'])
        self.assertEqual(len(self.cl), 1)
        
    def testAbsorbsDuplicates(self):
        self.assertEqual(len(self.cl), 0)
        self.cl.addCommand(CMD['c1'], dateTime('18:00:00'), USER['drewp'])
        self.cl.addCommand(CMD['c1'], dateTime('18:00:00'), USER['drewp'])
        self.assertEqual(len(self.cl), 1)

class TestCommandLogGraphInit(unittest.TestCase):
    def testUsesSingleGraphForRW(self):
        g1 = ConjunctiveGraph()
        c = CommandLog(Graph2(g1, initNs=INITNS))
        c.addCommand(CMD['c1'], dateTime('18:00:00'), USER['drewp'])
        self.assert_(len(g1) > 0)

    def testWritesToSeparateGraph(self):
        g1 = ConjunctiveGraph()
        g2 = ConjunctiveGraph()
        c = CommandLog(Graph2(g1, initNs=INITNS), Graph2(g2, initNs=INITNS))
        c.addCommand(CMD['c1'], dateTime('18:00:00'), USER['drewp'])
        self.assertEqual(len(g1), 0)
        self.assert_(len(g2) > 0)

class TestLogCustomQuery(WithGraph, unittest.TestCase):
    def setUp(self):
        super(TestLogCustomQuery, self).setUp()
        self.cl.addCommand(CMD['c1'], dateTime('18:00:00'), USER['drewp'])
        self.cl.addCommand(CMD['c2'], dateTime('18:01:00'), USER['drewp'])
        self.cl.addCommand(CMD['c3'], dateTime('18:02:00'), USER['drewp'])

    def testLen(self):
        self.assertEqual(len(self.cl), 3)
        self.cl.addCommand(CMD['c1'], dateTime('18:03:00'), USER['drewp'])
        self.assertEqual(len(self.cl), 4)
    
    def testRecentCommands(self):
        x = list(self.cl.recentCommands(2))
        y = [(CMD['c3'], dateTime('18:02:00'), USER['drewp']),
             (CMD['c2'], dateTime('18:01:00'), USER['drewp'])]
        print x[0][1], y[0][1]
        
        self.assertEqual(list(self.cl.recentCommands(2)),
                         [(CMD['c3'], dateTime('18:02:00'), USER['drewp']),
                          (CMD['c2'], dateTime('18:01:00'), USER['drewp'])])

    def testLastCommandOfClass(self):
        self.assertEqual(self.cl.lastCommandOfClass(CMD['Bright']),
                         (CMD['c2'], dateTime('18:01:00'), USER['drewp']))

    def testLastCommandNoData(self):
        self.assertRaises(ValueError,
                          self.cl.lastCommandOfClass, CMD['Nonexist'])
        

class TestPing(WithGraph, unittest.TestCase):
    def testSendsPing(self):
        pings = []
        
        self.cl = CommandLog(Graph2(self.graph, initNs=INITNS),
                             newCommandPing=lambda **kw: pings.append(kw))
        self.cl.addCommand(CMD['c2'], dateTime('18:00:00'), USER['drewp'])
        self.assertEqual(pings, [
            {'content': 'http://bigasterisk.com/command/http%3A//example.com/c2/1228183200.0/http%3A//example.com/user/drewp',
             'signal': 'http://example.com/Bright'}])

    def testSendsMultipleClasses(self):
        pings = []
        
        self.cl = CommandLog(Graph2(self.graph, initNs=INITNS),
                             newCommandPing=lambda **kw: pings.append(kw))
        self.graph.add((CMD['c2'], RDF.type, CMD['Volume'])) # second cls

        self.cl.addCommand(CMD['c2'], dateTime('18:00:00'), USER['drewp'])
        c = 'http://bigasterisk.com/command/http%3A//example.com/c2/1228183200.0/http%3A//example.com/user/drewp'
        self.assertEqual(sorted(pings), sorted([
            {'content': c, 'signal': 'http://example.com/Bright'},
            {'content': c, 'signal': 'http://example.com/Volume'}]))

    def testDoesntSendStrayClasses(self):
        pings = []
        self.graph.add((CMD['other'], RDF.type, CMD['Other']))
        self.cl = CommandLog(Graph2(self.graph, initNs=INITNS),
                             newCommandPing=lambda **kw: pings.append(kw))
        self.cl.addCommand(CMD['c2'], dateTime('18:00:00'), USER['drewp'])
        self.assertEqual(len(pings), 1)
        

# todo: times in different zones probably don't sort correctly unless
# the rdf store knows a lot about dates
