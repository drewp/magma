import restkit, logging, sys, urllib
log = logging.getLogger()

def httpGet(url, params):
    # restkit 3.3.2 returns empty string for this!
    return urllib.urlopen(url+"?"+urllib.urlencode(params)).read()

def _graphiteGet(target):
    # "http://graphite.bigasterisk.com/render/" normal url, but it logs requests
    data = httpGet("http://bang:9037/render", {
        'target':"keepLastValue(%s)" % target,
        'rawData':'true',
        'from':'-60minutes',
        })
    #headers={"user-agent":"%s _graphiteGet" % sys.argv[0]}, # sent this when using restkit

    v = data.split('|')[-1].split(',')[-1]
    return float(v)

def getAllTemps():
    lastTemp = {}
    for name in ['downstairs', 'bedroom', 'livingRoom', 'ariBedroom', 'frontDoor']:
        try:
            lastTemp[name] = _graphiteGet("system.house.temp.%s" % 
                                          name.replace('ariBedroom', 'ariroom'))
        except ValueError:
            log.error("temp failed: %r" % name)

    try:
        lastTemp['KSQL'] = _graphiteGet("system.noaa.ksql.temp_f")
    except ValueError:
        pass

    return lastTemp
