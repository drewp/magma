import sys
from twisted.python import log
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks

import txmongo
from txmongo import filter as qf
import cyclone.escape
import cyclone.web
import cyclone.websocket

class Chat(cyclone.websocket.WebSocketHandler):
    waiters = set()
    @inlineCallbacks
    def connectionMade(self):
        Chat.waiters.add(self)
        print "new", self
        yield self.sendHistory()

    def connectionLost(self, reason):
        Chat.waiters.remove(self)
        print "lost", self

    @inlineCallbacks
    def messageReceived(self, message):
        parsed = cyclone.escape.json_decode(message)
        log.msg("got message %r" % parsed)
        if parsed == {'req': 'reloadHistory'}:
            yield self.sendHistory()

    @inlineCallbacks
    def sendHistory(self):
        hist = yield self.settings.coll.find(filter=qf.sort(qf.DESCENDING('t')), limit=10)
        for row in hist:
            row['uri'] = row.pop('_id')
            row['t'] = row['t'].isoformat()
                                 
        self.sendMessage({'type': 'history', 'history': hist})
        
@inlineCallbacks
def main():
    conn = yield txmongo.MongoConnectionPool(host='bang', port=27017)
    
    reactor.listenTCP(3002, cyclone.web.Application(
        [
            (r"/chat", Chat),
        ],
        xsrf_cookies=True,
        coll=conn.magma.chat,
    ))


if __name__ == "__main__":
    log.startLogging(sys.stdout)
    main()
    reactor.run()
    
