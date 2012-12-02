#!/usr/bin/python
"""
proxy that serves multiple images as one concatenated one
"""
import bottle, restkit, urllib
import json, Image
from twisted.internet import reactor
from StringIO import StringIO

config = json.loads(open("imgCat.conf").read())

@bottle.route("/")
def index():
    return "imgcat: %r" % config

def urlFromDescription(desc):
    params = []
    for k,v in desc['params'].items():
        if isinstance(v, list):
            params.extend((k, x) for x in v)
        else:
            params.append((k, v))
    return desc['uri'] + "?" + urllib.urlencode(params)

@bottle.route("/cat/:which")
def cat(which):
    desc = config['output'][which]

    # should be parallel
    imgs = []
    for i in desc['inputs']:
        if isinstance(i, dict):
            i = urlFromDescription(i)
        response = restkit.request(i, headers={
            "Cookie" : bottle.request.headers.get('Cookie', '')
            }, follow_redirect=True)
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

    bottle.response.set_header("content-type", "image/jpeg" if not which.endswith('.png') else "image/png")
    save = StringIO()
    out.save(save, which.split('.')[-1].replace('jpg', 'jpeg'), **desc.get('saveOpts', {}))
    return save.getvalue()

bottle.run(server='gunicorn', host="0.0.0.0", port=8013, workers=4)
