"""
little table widget to include in other pages. Shows current events only.

argv has the port to serve on and the url to the sensu api server
(might be http://localhost:4567)

"""
import bottle, restkit, json, cgi, datetime, sys

sensu = restkit.Resource(sys.argv[2])

@bottle.route("/table")
def index():
    esc = cgi.escape
    out = '<table class="sensuEvents">'
    for event in json.loads(sensu.get("events").body_string()):
        issued = datetime.datetime.fromtimestamp(event['issued'])
        out += ('''
        <tr class="status%d">
          <td class="last">At %s</td>
          <td class="client">%s</td>
          <td class="check">%s</td>
          <td class="output">%s</td>
        </tr>''' % (
                    event['status'],
                    esc(issued.isoformat()),
                    esc(event['client'].split('.')[0]),
                    esc(event['check']),
                    esc(event['output'])))
    out += "</table>"
    return out

bottle.run(host='0.0.0.0', port=int(sys.argv[1]))


