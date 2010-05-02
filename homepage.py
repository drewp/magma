from __future__ import division
import sys, time, re, os, stat, jsonlib
from binascii import hexlify
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
from commandinference.db import XS
import iso8601, time

import stripchart
reload(stripchart)

CMD = Namespace("http://bigasterisk.com/magma/cmd/")
CL = Namespace("http://bigasterisk.com/ns/command/v1#")

    # if this is from a phone, use the little menu. the big menu
    # should also be ext, and have links to all the inner services.

class HomePage(rend.Page):
    docFactory = loaders.xmlfile("magma-sample2.html")
    def __init__(self, cmdlog, identity):
        """identity is an openid"""
        self.cmdlog = cmdlog
        self.graph = cmdlog.graph
        self.user = identity
        rend.Page.__init__(self)

    def locateChild(self, ctx, segments):
        req = inevow.IRequest(ctx)
        req.arg('login')

    def renderHTTP(self, ctx):
        req = inevow.IRequest(ctx)

        ua = req.getHeader('user-agent')
        # e.g. 'Mozilla/4.0 (compatible; MSIE 6.0; Windows 98; PalmSource/hspr-H102; Blazer/4.0) 16;320x320'
        self.blazer = 'Blazer' in ua
        
        return rend.Page.renderHTTP(self, ctx)


    def render_loginBar(self, ctx, data):
        return getPage("http://bang:9023/_loginBar", headers={
            "Cookie" : inevow.IRequest(ctx).getHeader("cookie")}
                       ).addCallback(T.raw)
        

    def render_commands(self, ctx, data):
        trs = [T.tr['']]
        for row in self.graph.queryd("""
         SELECT ?uri ?label ?icon ?linksTo WHERE {
           ?user cl:seesCommand ?uri .
           ?uri rdfs:label ?label .
           OPTIONAL { ?uri cl:iconPath ?icon }
           OPTIONAL { ?uri cl:linksTo ?linksTo }
         } ORDER BY ?label
        """, initBindings={Variable("user") : self.user}):

            if len(trs[-1].children) >= 1 + 3:
                trs.append(T.tr[''])
                
            button = row['label']
            if 'icon' in row:
                button = [T.img(src=row['icon'], alt=row['label']),
                          T.div(class_='label')[row['label']]]
                
            buttonClass = ''
            if row['uri'] in [CMD.BabyStart, CMD.BabyStop]:
                last, _, _ = self.cmdlog.lastCommandOfClass(CL.BabyStartStop)
                if last == row['uri']:
                    buttonClass += " current"
                else:
                    buttonClass += " recommend"

            if row.get('linksTo'):
                form = T.form(method="get", action=row['linksTo'])
                button = button + "..."
            else:
                form = T.form(method="post", action="addCommand")

            trs[-1].children.append(T.td[
                "\n", form[
                    T.input(type='hidden', name='uri', value=row['uri']),
                    T.button(class_=buttonClass)[button],
                ]])
        return T.table[trs]

    def child_addCommand(self, ctx):
        request = inevow.IRequest(ctx)
        if request.method != "POST":
            # there's a correct http status for this
            raise ValueError("addCommand only takes POST")

        # nevow has a better form than this, i hope
        request.content.seek(0)
        args = dict(url.unquerify(request.content.read()))

        t = iso8601.tostring(time.time(),
                             # using current timezone, even for passed-in value
                             (time.timezone, time.altzone)[time.daylight]) 
        cmd = self.cmdlog.addCommand(URIRef(args['uri']),
                               Literal(t, datatype=XS['dateTime']),
                               self.user)

        # accept: json for AJAX

        # this kind of stuff was not working on the url.here redirect:
        #request.received_headers['host'] = 'bigasterisk.com'
        #request.prepath = ['magma']
        #request.setHost('bigasterisk.com', 80)
        return url.URL.fromString('http://bigasterisk.com/magma').add('added', cmd)

    def render_addedCommand(self, ctx, data):
        if not ctx.arg('added'):
            return ''
        cmd = URIRef(ctx.arg('added'))

        rows = self.graph.queryd("""
          SELECT ?label ?time WHERE {
            ?issue dcterms:created ?time;
                   cl:command [
                     rdfs:label ?label
                   ]
          }""", initBindings={Variable("issue") : cmd})
        
        return T.div(class_='ranCommand')['Ran command %s at %s' %
                                          (rows[0]['label'], rows[0]['time'])]
        
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

    def render_currentMilli(self, ctx, data):
        return int(time.time() * 1000)

    def child_babyKick(self, ctx):
        return BabyKick(self.graph)

    def child_babyTable(self, ctx):
        return BabyTable(self.graph)

    def child_garage(self, ctx):
        return SecureButton(self.graph, self.cmdlog, self.user)

class BabyKick(stripchart.Chart):
    title = "Baby kicks"
    def __init__(self, graph):
        self.graph = graph
        
    def getData(self, ctx):
        rows = []

        for cmdN3, d in [
            ('cmd:BabyKick', {'label':'kick', 'marker' : T.raw('&#11030;')}),
            ('cmd:BabyStart', {'label':'start', 'marker' : T.raw('+')}),
            ('cmd:BabyStop', {'label':'stop', 'marker' : T.raw('-')}),
            ]:
            for row in self.graph.queryd("""
              SELECT DISTINCT ?t WHERE {
                [ cl:command %s;
                  dcterms:created ?t ;
                  a cl:IssuedCommand ]
              } ORDER BY ?t""" % cmdN3):
                t = iso8601.parse(row['t'])
                rows.append((t, None, d))
            
        print "found rows", rows
        return stripchart.Events(rows)
    
class BabyTable(rend.Page):
    addSlash = True
    docFactory = loaders.stan(T.html[T.head[
        T.title["Baby event table"],
        T.style(type="text/css")[T.raw('''
        body {
          width: 1000px;
          font-family: sans-serif;
          color: #333;
        }
        table { border-collapse: collapse; }
        td {
          white-space: nowrap;
          padding: 0 3px;
        }
        div.bar {
          position: relative;
          background: #eee;
        }
        div.bar .fill {
          position:absolute; 
        }
        div.bar .txt {
          position:absolute; 
        }
        ''')],
        T.meta( name="viewport",
                content="width=500; initial-scale=1.0; minimum-scale: .01; user-scalable=yes"),

        ], T.body[T.h1['Baby events'],
                  T.directive('table')]])
    def __init__(self, graph):
        self.graph = graph
        rend.Page.__init__(self)
        
    def render_table(self, ctx, data):
        rows = []
        for row in self.graph.queryd("""
          SELECT DISTINCT ?cmd ?t WHERE {
           {
             ?iss cl:command cmd:BabyStart .
           } UNION {
             ?iss cl:command cmd:BabyStop .
           }
           ?iss
              dcterms:created ?t ;
              cl:command ?cmd ;
              a cl:IssuedCommand .
           FILTER ( ?t > "2009-07-25T00:00:00Z"^^xs:dateTime )
          } ORDER BY ?t"""):
            t = iso8601.parse(row['t'])
            rows.append((t, row['cmd'], row['t']))

        label = {CMD.BabyStart : 'start',
                 CMD.BabyStop : 'stop'}

        def cleanTime(isot):
            m = re.match(r"^(....-..-..)T(..:..:..)", isot)
            return "%s %s" % (m.group(1), m.group(2))

        def prettyElapsed(sec):
            return "%.1f min" % (sec / 60)

        trs = []

        lastStart = None
        lastStop = None
        for row in rows:
            t, cmd, isot = row
            if cmd == CMD.BabyStart:
                if lastStart is not None:
                    period = t - lastStart[0]
                    cols = [
                        T.td[cleanTime(isot)],
                        T.td[divBar("%s since prev" % prettyElapsed(period),
                                    200, period / 600, "#f88")],
                        ]
                    if lastStop is not None:
                        dur = lastStop[0] - lastStart[0]
                        cols.append(T.td[
                            divBar("duration %s" % prettyElapsed(dur),
                                   150, dur / 200, "#8c3")])
                    trs.append(T.tr[cols])
                lastStart = row
                lastStop = None
            if cmd == CMD.BabyStop:
                lastStop = row
        
        return T.table[trs]

class SecureButton(rend.Page):
    addSlash = True
    docFactory = loaders.xmlfile("securebutton.html")    
    def __init__(self, graph, cmdlog, user):
        self.graph = graph
        self.cmdlog = cmdlog
        self.user = user
        self.ticketFile = "/tmp/garage-secret"
        self.lastCmd = ""
        rend.Page.__init__(self)

    @inlineCallbacks
    def renderHTTP(self, ctx):
        req = inevow.IRequest(ctx)
        if req.method == 'POST':
            try:
                if ctx.arg('ticket') != self.getTicket():
                    raise ValueError("incorrect access ticket")

                yield self.buttonPress()
                
                self.lastCmd = time.strftime("activated at %H:%M:%S")
            except ValueError, e:
                self.lastCmd = str(e)

        ret = yield rend.Page.renderHTTP(self, ctx)
        returnValue(ret)

    def buttonPress(self):
        """returns deferred"""
        print "go"

        t = iso8601.tostring(time.time(),
                    (time.timezone, time.altzone)[time.daylight]) 
        cmd = self.cmdlog.addCommand(
            URIRef("http://bigasterisk.com/magma/cmd/garageDoor"),
            Literal(t, datatype=XS['dateTime']),
            self.user)

        # the garage door also requires that bit 6 stay low, to avoid
        # false opens during bootup, when all pins go high for a while
        return getPage("http://slash:9014/otherBit?bit=7",
                       method="POST", headers={'Use-Agent' : 'magma'})


    def getTicket(self):
        t = jsonlib.loads(open(self.ticketFile).read(), use_float=True)

        if t['expires'] < time.time():
            raise ValueError("access ticket expired")
        return t['magic']

    def child_ticket(self, ctx):
        """one-time-use string to pass as ticket= param"""
        magic = hexlify(os.urandom(8))
        f = open(self.ticketFile, "w")
        os.chmod(self.ticketFile, stat.S_IRUSR | stat.S_IWUSR)
        f.write(jsonlib.dumps({'magic' : magic, 'expires' : time.time() + 5}))
        f.close()
        return magic

    def render_lastCmd(self, ctx, data):
        return self.lastCmd

def divBar(text, width, fraction, barColor):
    fraction = min(1, max(0, fraction))
    sp = T.raw('&nbsp;')
    return T.div(class_="bar", style="width: %spx;" % width)[
        T.div(class_="fill",
              style="width: %dpx; background: %s" % (width * fraction,
                                                     barColor))[sp],
        T.div(class_="txt")[text], sp]
    
