import restkit, logging, jsonlib
log = logging.getLogger()

def _graphiteGet(graphite, target):
    data = graphite.get('',
                        target="keepLastValue(%s)" % target,
                        rawData='true',
                        **{'from':'-60minutes'}).body_string()
    v = data.split('|')[-1].split(',')[-1]
    return float(v)

def getAllTemps():
    lastTemp = {}
    graphite = restkit.Resource("http://graphite.bigasterisk.com/render/")
    for name in ['downstairs', 'bedroom', 'livingRoom', 'ariBedroom', 'frontDoor']:
        try:
            lastTemp[name] = _graphiteGet(graphite, "system.house.temp.%s" % 
                                          name.replace('ariBedroom', 'ariroom'))
        except ValueError:
            log.error("temp failed: %r" % name)

    try:
        lastTemp['KSQL'] = _graphiteGet(graphite, "system.noaa.ksql.temp_f")
    except ValueError:
        pass

    return lastTemp
