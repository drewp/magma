import sys
from rdflib import Variable, Namespace, URIRef
import xmpp, twitter

FOAF = Namespace("http://xmlns.com/foaf/0.1/")
MB = Namespace("http://bigasterisk.com/ns/microblog/")

# from http://bigasterisk.com/darcs/?r=soundtrackbot;a=headblob;f=/streamingsoundtracks
class XmppSender(object):
    def __init__(self, jid, server, password):
        jid=xmpp.protocol.JID(jid)
        self.cl=xmpp.Client(jid.getDomain(),debug=[])
        if not self.cl.connect((server, 5222)):
            raise IOError('Can not connect to server.')
        if not self.cl.auth(jid.getNode(), password):
            raise IOError('Can not auth with server.')

    def sendMessage(self, recipient, text):
        self.cl.send(xmpp.Message(recipient, text, typ='chat'))

    def disconnect(self):
        self.cl.disconnect()
    __del__ = disconnect

def _getUserPass(graph, openid, accountType):
    rows = list(graph.queryd("""
      SELECT DISTINCT ?user ?password WHERE {
        ?id foaf:holdsAccount [
          a ?atype;
          foaf:accountName ?user;
          mb:password ?password
        ]
      }""", initBindings={Variable("id") : openid,
                          Variable("atype") : accountType}))
    if len(rows) != 1:
        raise ValueError("didn't find single user/password for %s "
                         "for %s" % (accountType, openid))
    return rows[0]

def postIdentica(graph, openid, msg):
    """
    uses openid's own jabberID and mb:jabberPassword to send to
    update@identi.ca (hopefully they are expecting messages from you)

    maybe there is a more standard way to POST an update to identica
    using your identica user/pass, or even openid (where we would be
    the providing party as well)
    """
    senderId = graph.value(openid, FOAF.jabberID)
    if senderId is None:
        raise ValueError("No foaf:jabberID found for %s" % openid)
    senderPassword = graph.value(openid, MB.jabberPassword)
    if senderPassword is None:
        raise ValueError("No mb:jabberPassword found for %s" % openid)
    
    senderServer = senderId.split('@')[1]
    sender = XmppSender(senderId, senderServer, senderPassword)
    sender.sendMessage("update@identi.ca", msg)

def postTwitter(graph, openid, msg):
    """
    openid is an RDF node that foaf:holdsAccount which is a mb:TwitterAccount
    """
    login = _getUserPass(graph, openid, MB.TwitterAccount)
    api = twitter.Api(username=login['user'], password=login['password'])
    status = api.PostUpdate(msg)

def postAll(graph, openid, msg):
    """post to all known services for this account. Return description
    of what happened (and maybe someday some RDF graph with links to
    the new posts"""
    # should query the graph and handle each service, but it's not
    # written that way yet
    postIdentica(graph, openid, msg) # errors here will interfere with twitter
    postTwitter(graph, openid, msg)
    return "posted to identica and twitter"

if __name__ == '__main__':
    sys.path.append('../photo')
    from remotesparql import RemoteSparql
    graph = RemoteSparql('http://plus:8080/openrdf-sesame/repositories', 'cmd',
                         dict(foaf=FOAF, mb=MB))

    postIdentica(graph, URIRef("http://bigasterisk.com/foaf.rdf#drewp"), 'test')
    postTwitter(graph, URIRef("http://bigasterisk.com/foaf.rdf#drewp"), 'test')
