from twisted.internet.defer import inlineCallbacks
from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate
from txamqp.content import Content
import txamqp.spec

@inlineCallbacks
def gotConnection(conn, authentication, body):
    yield conn.start(authentication)

    chan = yield conn.channel(1)
    yield chan.channel_open()

    msg = Content(body)
    msg["delivery mode"] = 2
    chan.basic_publish(exchange="sorting_room", content=msg, routing_key="jason")
    
    yield chan.channel_close()

    chan0 = yield conn.channel(0)
    yield chan0.connection_close()
    
    reactor.stop()
    
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print "%s path_to_spec content" % sys.argv[0]
        sys.exit(1)

    spec = txamqp.spec.load(sys.argv[1])

    authentication = {"LOGIN": "guest", "PASSWORD": "guest"}

    delegate = TwistedDelegate()
    d = ClientCreator(reactor, AMQClient, delegate=delegate, vhost="/",
        spec=spec).connectTCP("localhost", 5672)

    d.addCallback(gotConnection, authentication, sys.argv[2])


class Send(object):
    def __init__(self, host):

    def send(self, key, body):


class Receive(object):
    def __init___(self, host):

    
    def listen(self, key, func):
        
