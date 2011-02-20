import restkit, logging, jsonlib
log = logging.getLogger()

def getAllTemps():
    lastTemp = {}
    graphite = restkit.Resource("http://graphite.bigasterisk.com/render/")
    for name in ['downstairs', 'bedroom', 'livingRoom']:
        data = graphite.get('',
                            target="keepLastValue(system.house.temp.%s)" % name,
                            rawData='true',
                            **{'from':'-10minutes'}).body_string()
        v = data.split(',')[-1]
        try:
            lastTemp[name] = float(v)
        except ValueError:
            log.error("temp failed: %r -> %r" % (name, v))

    lastTemp['ariBedroom'] = jsonlib.read(
        restkit.request("http://star:9014/temperature").body_string(),
        use_float=True)['temp']
    return lastTemp
