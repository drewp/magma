import sys
sys.path.append('/usr/lib/python%s/site-packages/oldxml/_xmlplus/utils' %
                sys.version[:3])
import iso8601, time
from rdflib import URIRef, Literal
from nevow import inevow, url, json, rend
from db import XS

def returnPage(contentType, text):
    # why is this so hard! maybe i should use plain old t.w.resources?
    class Ret(rend.Page):
        def renderHTTP(self, ctx):
            request = inevow.IRequest(ctx)
            request.setHeader("Content-Type", contentType)
            return text
    return Ret()

class CommandSite(object): # mixin for rend.Page

    def __init__(self, cmdlog):
        self.cmdlog = cmdlog
        
    def child_addCommand(self, ctx):


        # this is obsoleted by a magma/addCommand handler

        
        request = inevow.IRequest(ctx)
        if request.method != "POST":
            # there's a correct http status for this
            raise ValueError("addCommand only takes POST")

        # nevow has a better form than this, i hope
        request.content.seek(0)
        args = dict(url.unquerify(request.content.read()))

        t = iso8601.tostring(float(args.get('time', time.time())),
                             # using current timezone, even for passed-in value
                             (time.timezone, time.altzone)[time.daylight]) 
        user = URIRef(args.get('user', 'http://bigasterisk.com/magma/user_tbd'))
        self.cmdlog.addCommand(URIRef(args['uri']),
                               Literal(t, datatype=XS['dateTime']),
                               user)

        return url.URL.fromString('http://bigasterisk.com/magma/heater/')# TODO#returnPage("text/javascript",
                       #   json.serialize({u'ok' : u'ok'})) # ??

    def child_history(self, ctx):
        cmds = list(self.cmdlog.recentCommands(10))
        ret = []
        for c, t, u in cmds:
            c = self.cmdlog.graph.label(c, default=c)
            ret.append((c, t, u))
        return returnPage("text/javascript", json.serialize(ret))

    def child_store(self, ctx):
        """
        since I don't have the negotiation stuff right, use this to
        see the store in N3:
        
        curl -s http://localhost:9014/store | cwm --rdf --n3
        """
        return returnPage("application/rdf+xml",
                          self.cmdlog.graph.serialize(format='xml'))

