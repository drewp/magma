"""
dispatcher-style API for amqp and twisted

This is a mangling of the examples from txamqp
"""

from twisted.internet.defer import inlineCallbacks, succeed, DeferredLock
from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from txamqp.protocol import AMQClient
from txamqp.client import TwistedDelegate
from txamqp.content import Content
import txamqp.spec

class Client(object):
    def __init__(self, specFilename, exchange='signals'):
        self.exchange = exchange
        spec = txamqp.spec.load(specFilename)

        delegate = TwistedDelegate()
        self.clientConnected = ClientCreator(reactor, AMQClient,
                                             delegate=delegate, vhost="/",
                                     spec=spec).connectTCP("localhost", 5672)
        self.conn = None
        self.chan = None
        self.finishLock = DeferredLock()

    @inlineCallbacks
    def finishChannelOpen(self):
        yield self.finishLock.acquire()
        if self.conn is None:
            print "opening connection for", self
            self.conn = yield self.clientConnected

            authentication = {"LOGIN": "guest", "PASSWORD": "guest"}
            yield self.conn.start(authentication)

        if self.chan is None:
            self.chan = yield self.conn.channel(1)
            yield self.chan.channel_open()
            yield self.newChan()
            print "made channel for", self
        self.finishLock.release()
            
    def newChan(self):
        # called once when the new channel is opened
        return succeed(None)

class Send(Client):
    @inlineCallbacks
    def send(self, key, body):
        """
        send a message with the given routing key, returns deferred,
        but the message isn't necessarily sent by the time the
        deferred fires since I don't know when that point is.
        """
        yield self.finishChannelOpen()


        print "sending", (key, body)
        msg = Content(body)
        msg["delivery mode"] = 2
        self.chan.basic_publish(exchange=self.exchange, content=msg,
                                routing_key=key)
        
    def close(self):
        yield self.chan.channel_close()
        chan0 = yield self.conn.channel(0)
        yield chan0.connection_close()

class Receive(Client):
    @inlineCallbacks
    def newChan(self):
        yield self.chan.exchange_declare(exchange=self.exchange,
                                         type="direct", durable=True,
                                         auto_delete=False)
        
    @inlineCallbacks
    def listen(self, key, func):
        """func will be called with key and body strings, where the
        key matches the one you pass in"""
        yield self.finishChannelOpen()

        yield self.chan.queue_declare(queue="q-"+key, durable=True,
                                      exclusive=False, auto_delete=False)
        yield self.chan.queue_bind(queue="q-"+key, exchange=self.exchange,
                                   routing_key=key)

        yield self.chan.basic_consume(queue="q-"+key, no_ack=True,
                                      consumer_tag="tag-"+key)

        queue = yield self.conn.queue("tag-"+key)
        while True:
            msg = yield queue.get()
            func(key, msg.content.body)

    def close(self):
        print "cancel"
        yield self.chan.basic_cancel("testtag")

        yield self.chan.channel_close()
        chan0 = yield self.conn.channel(0)
        yield chan0.connection_close()


if __name__ == '__main__':
    if 1:
        s = Send('/home/drewp/dl/txamqp_example/amqp0-8.xml', 'sorting_room')
        s.send('jason', 'v13')
        s.send('k2', 'k2body3')
        reactor.callLater(2, s.send, 'jason', 'm23')

    if 1:
        r = Receive('/home/drewp/dl/txamqp_example/amqp0-8.xml', 'sorting_room')
        def prn(key, body):
            print "heard", key, body
        r.listen('jason', prn)
        r.listen('k2', prn)
        r.listen('hi', prn)
        r.listen('http://bigasterisk.com/ns/command/v1#Command', prn)

    reactor.run()
