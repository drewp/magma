from nevow import rend, loaders
from pprint import pprint
from twisted.internet import reactor
from twisted.python import log
from twisted.python.util import sibpath
from twisted.web.client import getPage
from twisted.internet.defer import inlineCallbacks, returnValue
from nevow.appserver import NevowSite
from nevow import rend, static, loaders, tags as T, inevow, json, url
from rdflib import URIRef, Namespace, Variable, RDFS, Literal
from commandpage.db import XS
import iso8601, time

CMD = Namespace("http://bigasterisk.com/ns/command/v1#")


    # if this is from a phone, use the little menu. the big menu
    # should also be ext, and have links to all the inner services.
    
class HomePage(rend.Page):
    docFactory = loaders.xmlfile("magma-sample2.html")
    def __init__(self, graph, identity):
        self.graph = graph
        self.user = self.graph.subjects(CMD.openid, URIRef(identity)).next()
        rend.Page.__init__(self)

    def locateChild(self, ctx, segments):
        req = inevow.IRequest(ctx)
        req.arg('login')

    def renderHTTP(self, ctx):
        req = inevow.IRequest(ctx)
        pprint(req.__dict__)

        ua = req.getHeader('user-agent')
        # e.g. 'Mozilla/4.0 (compatible; MSIE 6.0; Windows 98; PalmSource/hspr-H102; Blazer/4.0) 16;320x320'
        self.blazer = 'Blazer' in ua
        
        return rend.Page.renderHTTP(self, ctx)

    def render_user(self, ctx, data):
        return self.user

    def render_commands(self, ctx, data):
        for uri, label in self.graph.query("""
         SELECT ?uri ?label WHERE {
           ?user cmd:seesCommand ?uri .
           ?uri rdfs:label ?label .
         } ORDER BY ?label
        """, initNs=dict(cmd=CMD, rdfs=RDFS.RDFSNS),
             initBindings={Variable("user") : self.user}):
            yield T.form(method="post", action="addCommand")[
                T.input(type='hidden', name='uri', value=uri),
                T.input(type='submit', value=label),
                ]

    def child_addCommand(self, ctx):
        request = inevow.IRequest(ctx)
        if request.method != "POST":
            # there's a correct http status for this
            raise ValueError("addCommand only takes POST")

        # nevow has a better form than this, i hope
        request.content.seek(0)
        args = dict(url.unquerify(request.content.read()))

        t = iso8601.tostring(float(args.get('time')),
                             # using current timezone, even for passed-in value
                             (time.timezone, time.altzone)[time.daylight]) 
        self.cmdlog.addCommand(URIRef(args['uri']),
                               Literal(t, datatype=XS['dateTime']),
                               self.user)

        return url.URL.fromString('http://bigasterisk.com/magma/heater/')# TODO#returnPage("text/javascript",
                       #   json.serialize({u'ok' : u'ok'})) # ??

    @inlineCallbacks
    def render_lights(self, ctx, data):

        @inlineCallbacks
        def line(queryName, label):
            ret = json.parse((yield getPage(
                "http://bigasterisk.com/magma/light/state?name=%s" % queryName,
                headers={'x-identity-forward' :
                         'secret-8-' + self.identity})))

            currently = ret['value']
            returnValue(T.form(method="POST", action="light/state")[
                T.input(type="hidden", name="name", value=queryName),
                T.div[label, " ", T.span[currently], ", turn ",
                      T.input(type="submit", name="value",
                              value="off" if currently=='on' else "on")]])

        # deferredlist!
        returnValue([(yield line("bedroomred", "bedroom light")),
                     (yield line("deck", "deck lights"))])
    
    def render_showMunin(self, ctx, data):
        if self.user == URIRef('http://bigasterisk.com/foaf.rdf#drewp') and not self.blazer:
            return ctx.tag
        
        return ''

    def render_showTwitters(self, ctx, data):
        if self.user == URIRef('http://bigasterisk.com/foaf.rdf#drewp') and not self.blazer:
            return ctx.tag
        return ''
