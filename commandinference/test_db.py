from twisted.trial import unittest
from rdflib import Namespace, Literal, RDF
from rdflib.Graph import Graph
from db import CommandLog

CMD = Namespace("http://example.com/")
USER = Namespace("http://example.com/user/")
XS = Namespace("http://www.w3.org/2001/XMLSchema#")

def dateTime(timeStr):
    return Literal("2008-12-01T%s-08:00" % timeStr, datatype=XS['dateTime'])

class WithGraph(object):
    def setUp(self):
        super(WithGraph, self).setUp()
        self.graph = Graph()
        self.graph.add((CMD['c2'], RDF.type, CMD['Bright']))
        self.cl = CommandLog(self.graph)

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

# todo: times in different zones probably don't sort correctly unless
# the rdf store knows a lot about dates
