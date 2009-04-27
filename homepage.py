from nevow import rend, loaders
from pprint import pprint
from twisted.internet import reactor
from twisted.python import log
from twisted.python.util import sibpath
from twisted.web.client import getPage
from twisted.internet.defer import inlineCallbacks, returnValue
from nevow.appserver import NevowSite
from nevow import rend, static, loaders, tags as T, inevow, json

    # if this is from a phone, use the little menu. the big menu
    # should also be ext, and have links to all the inner services.
    
class HomePage(rend.Page):
    docFactory = loaders.xmlfile("magma-sample2.html")

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
        return self.identity

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
        if self.blazer:
            return ''
        return ctx.tag

    def render_showTwitters(self, ctx, data):
        if self.identity == 'http://bigasterisk.com/' and not self.blazer:
            return ctx.tag
        return ''
