#!/usr/bin/python
"""
proxy that serves multiple images as one concatenated one

"""
import cyclone.web, restkit
import json, Image
from twisted.internet import reactor
from StringIO import StringIO

class Index(cyclone.web.RequestHandler):
    def get(self):
        self.write("imgcat: %r" % self.settings.config)

class Cat(cyclone.web.RequestHandler):
    def get(self, which):
        desc = self.settings.config['output'][which]

        # should be parallel
        imgs = []
        for i in desc['inputs']:
            response = restkit.request(i, headers={
                "Cookie" : self.request.headers.get('Cookie', '')
                })
            if response.status_int != 200:
                raise ValueError("fetching %s -> %s" % (i, response.status))
            data = response.body_string()
            img = Image.open(StringIO(data))
            if desc.get('resize', None) is not None:
                img.thumbnail((32000, desc['resize']['height']), Image.ANTIALIAS)
            imgs.append(img)

        outSize = max(i.size[0] for i in imgs), sum(i.size[1] for i in imgs)
        out = Image.new('RGB', outSize)
        y = 0
        for i in imgs:
            out.paste(i, (0, y))
            y = y + i.size[1]

        out.save(self, which.split('.')[-1].replace('jpg', 'jpeg'), **desc.get('saveOpts', {}))

if __name__ == '__main__':
    reactor.listenTCP(8013, cyclone.web.Application(
        handlers=[(r"/", Index),
                  (r"/cat/(.*)", Cat),
                  ],
        config=json.loads(open("imgCat.conf").read())))
    reactor.run()
