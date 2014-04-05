import sys, logging
from twisted.python import log as twlog
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from dateutil.parser import parse
from dateutil.tz import tzutc

import txmongo
from txmongo import filter as qf
import cyclone.escape
import cyclone.web
import cyclone.websocket

log = logging.getLogger()
logging.basicConfig(level=logging.INFO)

class Chat(cyclone.websocket.WebSocketHandler):
    waiters = set()
    @inlineCallbacks
    def connectionMade(self):
        Chat.waiters.add(self)
        self.agent = self.request.headers['x-foaf-agent']
        log.info("connect from %s", self.agent)
        yield self.sendHistory()

    def connectionLost(self, reason):
        log.info("lost connection from %s, %s",
                 getattr(self, 'agent', ''), reason)
        Chat.waiters.remove(self)

    @inlineCallbacks
    def messageReceived(self, message):
        parsed = cyclone.escape.json_decode(message)
        log.info("got message from %s: %r", self.agent, parsed)
        if parsed == {'type': 'reloadHistory'}:
            yield self.sendHistory()
            return
        if parsed['type'] == 'post':
            row = parsed['row']
            row['creator'] = self.agent
            row['to'] = self._whoTo(row['creator'])
            if not set(row.keys()).issuperset(
                    set(['uri', 't', 'creator', 'to', 'html'])):
                raise ValueError('missing fields')
            doc = row.copy()
            doc['_id'] = doc.pop('uri')
            doc['t'] = parse(doc['t'])
            yield self.settings.coll.insert(doc, safe=True)

        if parsed['type'] == 'connected':
            pass # return who is connected from where
            
        # temporary demo
        for w in self.waiters:
            w.sendHistory()

    def _whoTo(self, creator):
        # todo
        D = "http://bigasterisk.com/foaf.rdf#drewp"
        K = "http://bigasterisk.com/kelsi/foaf.rdf#kelsi"
        return {
            D: [K],
            K: [D],
        }[creator]
                
    @inlineCallbacks
    def sendHistory(self):
        hist = yield self.settings.coll.find(
            filter=qf.sort(qf.DESCENDING('t')), limit=10)
        for row in hist:
            row['uri'] = row.pop('_id')
            row['t'] = row['t'].replace(tzinfo=tzutc()).isoformat()
        hist.reverse()
                                 
        self.sendMessage({'type': 'history', 'you': self.agent, 'history': hist})
        
@inlineCallbacks
def main():
    conn = yield txmongo.MongoConnectionPool(host='bang', port=27017)
    
    reactor.listenTCP(8015, cyclone.web.Application(
        [
            (r"/chat/", Chat),
        ],
        xsrf_cookies=True,
        coll=conn.magma.chat,
    ))


if __name__ == "__main__":
    twlog.startLogging(sys.stdout)
    main()
    reactor.run()
    
