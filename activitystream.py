import urllib, simplejson
from nevow.tags import Tag
from nevow import flat, rend, inevow

class ActivityStream(object):
    """
    renders your activities into an ATOM activity stream.

    I'm trying to keep the API so it can support caching, if it's
    easier for you to insert new items only.
    """
    def __init__(self):
        self.entries = []

    def addEntry(self, actorUri, actorName,
                 verbUri, verbEnglish,
                 objectUri, objectName,
                 published,
                 objectIcon=None,
                 entryUri=None, entryUriComponents=()):
        """
        published is a datetime with zone.

        order of adds doesn't matter; we sort by 'published' later

        if entryUri is None, entryUriComponents should be any
        components *besides the publish time* that are needed to make
        a unique id. A word for the type of stream would be good, plus
        whatever else you need.
        """

        if entryUri is None:
            comps = (published.strftime("%s"),) + entryUriComponents
            entryUri = "http://bigasterisk.com/activity/id/%s" % (
                '/'.join(urllib.quote(comp.encode('ascii', 'ignore'), safe='')
                         for comp in comps))

        desc = "%s %s %s" % (actorName, verbEnglish, objectName)

        self.entries.append(vars())

    def entryAsStan(self, e):
        
        objIcon = []
        if e['objectIcon'] is not None:
            objIcon = Tag('link')(rel="icon", type="image/png",
                                  href=e['objectIcon'])

        entry = Tag('entry')[
            Tag('id')[e['entryUri']],

            Tag('author')[
                Tag('name')[e['actorName']],
                Tag('link')(rel='alternate', type='text/html',
                            href=e['actorUri']),
                ],
            
            Tag('activity:verb')[e['verbUri']],

            Tag('activity:object')[
                Tag('id')[e['objectUri']],
                Tag('name')[e['objectName']],
                objIcon,
                ],

            Tag('title')[e['desc']],
            Tag('content')(type="html")[e['desc']],
            Tag('published')[e['published'].isoformat()]
            ]
        return entry

    def entryAsJsonObj(self, e):
        return 

    def makeAtom(self):
        doc = Tag('atom')(**{
                'xmlns':'http://www.w3.org/2005/Atom', 
                'xmlns:activity':'http://activitystrea.ms/spec/1.0/'})

        self.entries.sort(key=lambda e: e['published'])
        doc[map(self.entryAsStan, self.entries)]
        return flat.flatten(doc)

    def makeJson(self):
        # i think i'm not going to write this, and use activity_merge instead
        return simplejson.dumps({
            'activities' : [
                {
                    'actor' : {
                        
                        },
                    'verb' : {

                        },
                    'object' : {
                        
                        },
                    'title' : "html",
                    }
                ]
            })
    
    def makeNevowResource(self):
        """
        a rend.Page with your atom or json feed, according to Accept
        """
        out = self.makeAtom()
        class Ret(rend.Page):
            def renderHTTP(self, ctx):
                
                inevow.IRequest(ctx).setHeader("Content-Type",
                                               "application/atom+xml")
                return out
        return Ret()
        
    def makeWebpyResponse(self, environ):
        # look at Accept header, call web.header, etc
        import web
        web.header("Content-type", "application/atom+xml")
        return self.makeAtom()
