import os
import json
import traceback
import klein
import datetime
from autobahn.twisted.websocket import WebSocketServerProtocol, WebSocketServerFactory
from autobahn.twisted.resource import WebSocketResource
from autobahn.websocket.types import ConnectionDeny
from twisted.web.static import File
import pymongo.mongo_client

import sys
sys.path.append('/my/proj/openid_proxy')
import rdfaccess

class Chats(object):
    def __init__(self):
        client = pymongo.mongo_client.MongoClient(host='bang6', tz_aware=True)
        client.database_names() # fail on missing mongo
        self.coll = client.get_database('magma').get_collection('chat')

        self.access = rdfaccess.Access()
        
    def rooms(self):
        out = []
        # should use room collection with invited people
        for room in self.coll.distinct('room'):
            agents = self.coll.distinct('creator', filter={'room': room})
            names = map(self.foafName, agents)
            lastLine = self.coll.find_one({'room': room}, sort=[('t', -1)])
            if lastLine:
                lastTime = lastLine['t'].timestamp() * 1000
            else:
                lastTime = 'never'
            out.append({'label': room, 'uri': room, 'users': ', '.join(sorted(names)), 'lastLineMilli': lastTime})
        return out

    def foafName(self, uri):
        return self.access.foafName(rdfaccess.AgentUri(uri))
        
    def messages(self, room):
        if not room:
            return {}
        rows = [
            {
                'author': self.foafName(m['creator']),
                'text': m['text'],
                'created': m['t'].isoformat(),
            } for m in self.coll.find({'room': room},
                                      sort=[('t', -1)],
                                      limit=100)]
        rows.reverse()
        return {'room': room, 'rows': rows}
        
    def post(self, agent, q):
        # check that user can write to room
        doc = {'t': datetime.datetime.utcnow(),
               'creator': agent,
               'room': q['room'],
               'text': q['text'],
               }
        print('post', doc)
        self.coll.insert_one(doc)
        return {'saved': True}

listeners = set()
        
class MessagesSocketProtocol(WebSocketServerProtocol):

    def sendJson(self, d):
        try:
            j = json.dumps(d)
        except:
            traceback.print_exc()
            raise
        self.sendMessage(j.encode('utf8'), isBinary=False)
        
    def onConnect(self, request):
        try:
            self.agent = request.headers['x-foaf-agent']
        except KeyError:
            raise ConnectionDeny(code=401, reason='login required')
        print('WS connection from agent ', self.agent)
        listeners.add(self)
        
    def onOpen(self):
        print("WebSocket connection open.")
        self.focusRoom = None
        self.sendJson({
            'me': {'agent': self.agent,
                   'foafName': chats.foafName(self.agent),
                   },
            'rooms': chats.rooms(),
        })

    def onMessage(self, payload, isBinary):
        if isBinary:
            print("Binary message received: {0} bytes".format(len(payload)))
            return
            
        self.onParsedMessage(json.loads(payload.decode('utf8')))

    def onParsedMessage(self, msg):
        if 'focusRoom' in msg:
            self.focusRoom = msg['focusRoom']
            self.sendJson({'messages': chats.messages(self.focusRoom)})
        if 'post' in msg:
            self.sendJson(chats.post(self.agent, msg['post']))

            m = chats.messages(msg['post']['room'])
            for l in listeners:
                l.sendJson({'messages': m})

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {0}".format(reason))
        listeners.remove(self)
        print("%s listeners left" % len(listeners))
        
chats = Chats()
port = 8011
loginPage = 'https://bigasterisk.com/chat/login?redir=https://bigasterisk.com/chat/'
        
factory = WebSocketServerFactory(u"ws://127.0.0.1:%s" % port)
factory.protocol = MessagesSocketProtocol
resource = WebSocketResource(factory)

@klein.route('/messages')
def ws(request):
    return resource

@klein.route('/', branch=True)
def root(request):
    if not request.getHeader('x-foaf-agent'):
        request.setResponseCode(307)
        request.setHeader('location', loginPage)
        return
    
    if b'.' not in request.path:
        print('%r appears to be a polymer route' % request.path)
        request.path = b'/'
        request.uri = b'/'
        request.postpath = [b'']
    root = b'./'
    if os.path.exists(b'build/es6-bundled%s' % request.path):
        return File('./build/es6-bundled/')
    return File('./')

klein.run('0.0.0.0', port)

