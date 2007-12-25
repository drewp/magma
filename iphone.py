#!/usr/bin/python
import os, sys
from twisted.internet import reactor
from twisted.python import log
from twisted.python.util import sibpath
from nevow.appserver import NevowSite
from nevow import rend, static, loaders, tags as T, inevow, json, url

class IphonePage(rend.Page):
    addSlash = True
    title = None
    items = []
    docFactory = loaders.xmlstr('''\
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
     "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">

<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:n="http://nevow.com/ns/nevow/0.1">
<head>
<title>iPhone Navigation</title>
<meta name="viewport" content="width=320; initial-scale=1.0; maximum-scale=1.0; user-scalable=0;"/>
<style type="text/css" media="screen">@import "/iui/iui.css";</style>
<script type="application/x-javascript" src="/iui/iuix.js"></script>
</head>

    <body n:render="body"/>
    </html>
    ''')
    def render_body(self, ctx, data):
        title = self.title
        if title is None:
            title = self.__class__.__name__
        return ctx.tag[
            T.div(class_="toolbar")[
              T.h1(class_="pageTitle")[title],
              T.a(id="backButton", class_="button", href="/")['Top'],
              ],
            T.ul(selected="true")[
              [T.li[x] for x in self.getItems(ctx)]]]
    def getItems(self, ctx):
        return self.items

class Heater(IphonePage):
    items = ['Status: on', T.a(href='history')['History']]
    def child_history(self, ctx):
        class History(IphonePage):
            title = "Heater Log"
            items = ['Last on 08:50',
                     'On for 3.3h today',
                     'Avg 4.5h/day this week']
        return History()

class Door(IphonePage):
    def getItems(self, ctx):
        return ['Locked now',
                T.a(href='unlock1m')['Unlock for 1m'],
                ]
    def child_unlock1m(self, ctx):
        print "unlock now"
        return url.here.up()

class Music(IphonePage):
    docFactory = loaders.xmlstr("""<div title="Story">
    <li><a href="">one</a></li>
    <li>two</li>
    <h2>10 Alternatives to iTunes for managing your iPod</h2>
    <p>This overview details the features (with screenshots) of 10 different programs other than iTunes to manage your iPod. Tutorials are included for every program, and theyre all either free or Open Sour
ce.</p>
</div>""")
    items = ['one', 'two']
        
class Main(IphonePage):
    title = "Home Controls"
    subMenus = [Heater, Door, Music]
    def getItems(self, ctx):
        for sub in self.subMenus:
            name = sub.__name__
            yield T.a(href=name + "/")[name]

    def locateChild(self, ctx, segments):
        print segments
        if segments == ('iui', 'iui.css'):
            txt = open("iui/iui/iui.css").read()
            txt = txt.replace("url(", "url(/iui/")
            print "rewrite", len(txt)
            return static.Data(txt, 'text/css'), []
        
        d = dict([(s.__name__, s) for s in self.subMenus])
        if segments[0] in d:
            cls = d[segments[0]]
            return cls(), segments[1:]
        return rend.Page.locateChild(self, ctx, segments)
    def child_iui(self, ctx):
        return static.File("iui/iui")
setattr(Main, 'child_facicon.ico', static.File('favicon.ico'))

if __name__ == '__main__':
    log.startLogging(sys.stdout)
    reactor.listenTCP(8006, NevowSite(Main()))
    reactor.run()
