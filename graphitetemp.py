import restkit, logging, jsonlib
log = logging.getLogger()

def _graphiteGet(graphite, target):
    data = graphite.get('',
                        target="keepLastValue(%s)" % target,
                        rawData='true',
                        **{'from':'-10minutes'}).body_string()
    v = data.split(',')[-1]
    return float(v)

def getAllTemps():
    lastTemp = {}
    graphite = restkit.Resource("http://graphite.bigasterisk.com/render/")
    for name in ['downstairs', 'bedroom', 'livingRoom']:
        try:
            lastTemp[name] = _graphiteGet(graphite, "system.house.temp.%s" % name)
        except ValueError:
            log.error("temp failed: %r" % name)

    try:
        lastTemp['KSQL'] = _graphiteGet(graphite, "system.noaa.ksql.temp_f")
    except ValueError:
        pass

    lastTemp['ariBedroom'] = jsonlib.read(
        restkit.request("http://star:9014/temperature").body_string(),
        use_float=True)['temp']
    return lastTemp
