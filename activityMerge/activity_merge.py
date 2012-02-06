#!/usr/bin/python
"""
combines multiple activity stream ATOM feeds and sorts them by time,
to make a new AS feed or html listing

config:
 {
    feeds: {
      'feed1' : { sources: ['http://upstream1', 'http://upstream2'] },
      ...
    }
 }

Fetch
/f/feed1 Accept: application/atom+xml or .atom extension
  -> new atom
/f/feed1?order=desc Accept: application/xhtml+xml or .xhtml extension
  -> xhtml results

Your request's x-foaf-agent header is forwarded to the upstream feeds.
"""
import web, restkit, simplejson
from lxml import etree
from dateutil.parser import parse
from nevow.tags import Tag
from nevow import flat

ATOM = '{http://www.w3.org/2005/Atom}'
ACTIVITY = '{http://activitystrea.ms/spec/1.0/}'

config = simplejson.load(open("activity.json"))

class index(object):
    def GET(self):
        web.header('content-type', 'text/plain')
        return "activity_merge server: %s" % config

class feed(object):
    def GET(self, name, ext=None):
        ext = self.pickFormat(ext, web.ctx.environ.get('HTTP_ACCEPT',''))

        sources = self.getSources(name)

        entries = self.getAllEntries(name, sources)

        if ext == 'atom':
            web.header('content-type', 'application/atom+xml')
            return self.makeAtom(entries, sources)
        elif ext == 'xhtml':
            web.header('content-type', 'application/xhtml+xml')
            return self.makeXhtml(entries, sources,
                                  order=web.input().get('order','asc'))
        elif ext == 'json':
            web.header('content-type', 'application/json')
            return self.makeJson(entries, sources)
        else:
            raise NotImplementedError

    def pickFormat(self, providedExtension, acceptHeader):
        if providedExtension is not None:
            return providedExtension
        if acceptHeader.startswith('application/xhtml+xml'):
            return 'xhtml'
        elif (acceptHeader.startswith('application/atom+xml') or 
              acceptHeader in ['*/*', '']):
            return 'atom'
        elif acceptHeader.startswith(('application/json', 'text/plain')):
            return 'json'

        raise NotImplementedError(
            "My Accept header parser sucks (%r)" % acceptHeader)

    def getSources(self, name):
        conf = config['feeds'][name]
        return conf['sources']
    
    def getAllEntries(self, name, sources):
        """
        returns etree <entry> nodes, sorted in ascending time order
        """
        entries = []
        requests = []
        for source in sources:
            headers = {'user-agent' : 'activity_merge'}
            if web.ctx.environ.get('HTTP_X_FOAF_AGENT', ''):
                headers['x-foaf-agent'] = web.ctx.environ['HTTP_X_FOAF_AGENT']
            requests.append(restkit.request(source, headers=headers))

        for req in requests:
            atom = req.body_string()
            entries.extend(etree.fromstring(atom).iter(ATOM+'entry'))

        entries.sort(key=lambda e: parse(e.findtext(ATOM+'published')))
        return entries

    def makeAtom(self, entries, sources):
        root = etree.XML("<atom/>")
        for e in entries:
            root.append(e)
        return etree.tostring(root)

    def makeXhtml(self, entries, sources, order='asc'):
        root = Tag('ul')
        if order == 'desc':
            entries = entries[::-1]
        for e in entries:
            item = Tag('li')
            published = e.findtext(ATOM+'published')
            root[item[e.findtext(ATOM+'title'), 
                      Tag('div')(class_="published", 
                            milli=jsonMilliFromIsoTime(published))[published]]]

        return flat.flatten(root)

    def makeJson(self, entries, sources):
        # see http://activitystrea.ms/head/json-activity.html

        def entryDict(e):
            a = e.find(ATOM+"author")
            actor = {'name' : a.findtext(ATOM+"name"),
                     'link' : a.find(ATOM+"link").attrib['href']}
            
            verb = e.findtext(ACTIVITY+"verb")
            o = e.find(ACTIVITY+"object")
            object = {'id' : o.findtext(ATOM+"id"), # right ns?
                      'name' : o.findtext(ATOM+"name"),
                      }
            imgLink = o.find(ATOM+"link")
            icon = ''
            if imgLink and imgLink.attrib['rel'] == 'icon': # now 'preview'? this needs loop
                icon = imgLink.attrib['href']
                object['image'] = imgLink.attrib['href']
            title = e.findtext(ATOM+'title')
            return {'actor' : actor,
                    'verb' : verb,
                    'object' : object,
                    'title' : title,
                    'icon' : icon,
                    'postedTime' : e.findtext(ATOM+"published"),
                    }
        
        return simplejson.dumps({
            # wrong, see http://activitystrea.ms/head/activity-api.html#anchor4
            'sources' : sources,
            'activities' : [entryDict(e) for e in entries]
            })

def jsonMilliFromIsoTime(s):
    dt = parse(s)
    secs = float(dt.strftime('%s'))
    return int(secs * 1000)

urls = (
    r'/', 'index',
    r'/f/(.*?)(?:\.([^\.]+))?$', 'feed',
)

if __name__ == '__main__':
    app = web.application(urls, globals(), autoreload=True)
    app.run()
