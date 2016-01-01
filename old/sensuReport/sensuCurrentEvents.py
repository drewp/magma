"""
little table widget to include in other pages. Shows current events only.

argv has the port to serve on and the url to the sensu api server
(might be http://localhost:4567)

"""
import bottle, restkit, json, cgi, time, sys

sensu = restkit.Resource(sys.argv[2])

@bottle.route("/")
def index():
    return '<a href="table">table</a>'

@bottle.route("/table")
def table():
    esc = cgi.escape
    out = '<table class="sensuEvents">'
    for event in json.loads(sensu.get("events").body_string()):
        withinMins = round((time.time() - event['issued']) / 60., 1)
        out += ('''
        <tr class="status%d">
          <td class="last">Within <span>%.1f %s</span></td>
          <td class="client">%s</td>
          <td class="check">%s</td>
          <td class="output">%s</td>
        </tr>''' % (
                    event['status'],
                    withinMins,
                    "min" if withinMins == 1.0 else "mins",
                    esc(event['client'].split('.')[0]),
                    esc(event['check']),
                    esc(event['output'])))
    out += "</table>"
    return out

bottle.run(host='0.0.0.0', port=int(sys.argv[1]))


