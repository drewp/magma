import sys
from rdflib import Variable, Namespace, URIRef
from getpass import getpass
# easy_install 'python-twitter', and don't have the one called 'twitter' around
import xmpp, twitter, jsonlib, urllib
import restkit

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
          a ?atype ;
          foaf:accountName ?user ;
          mb:password ?password
        ]
      }""", initBindings={Variable("id") : openid,
                          Variable("atype") : accountType}))
    if len(rows) != 1:
        raise ValueError("found %s user/password pairs for %s "
                         "for %s" % (len(rows), accountType, openid))
    return rows[0]

def postIdenticaXmpp(graph, openid, msg):
    """
    uses openid's own jabberID and mb:jabberPassword to send to
    update@identi.ca (hopefully they are expecting messages from you)

    maybe there is a more standard way to POST an update to identica
    using your identica user/pass, or even openid (where we would be
    the providing party as well)

    alternate:
    http://bitbucket.org/waltercruz/feed2mb/src/tip/feed2mb/feed2mb/microblog.py
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


def postIdenticaOauth():
    """ not working yet. last tried on 2010-05 """
    from restkit import OAuthFilter, request
    import restkit.oauth2 

    consumer = restkit.oauth2.Consumer(key=oauthKey, secret=oauthSecret)

    request_token_url = "http://identi.ca/api/oauth/request_token"

    auth = OAuthFilter(('*', consumer))

    if 1:
        # The request.
        resp = request(request_token_url, filters=[auth])
        print resp.__dict__
        print resp.body
    else:
        tok = restkit.oauth2.Token(oauth_token, oauth_token_secret)

    resp = restkit.request(
        "http://identi.ca/api/statuses/friends_timeline.json",
        filters=[OAuthFilter(('*', consumer, tok))],
        method="GET")
    print resp.body
    print resp

    resp = restkit.request("http://identi.ca/api/statuses/update.json",
                    filters=[OAuthFilter(('*', consumer, tok))],
                    method="POST",
                    body=jsonlib.dumps({'status' : 'first oauth update'}))

    print resp.body
    print resp

def postIdenticaPassword(graph, openid, msg):
    login = _getUserPass(graph, openid, MB.IdenticaAccount)
    api = restkit.Resource("http://identi.ca/api",
                           filters=[restkit.BasicAuth(login['user'],
                                                      login['password'])])
    resp = api.post("statuses/update.json", status=msg)
    return jsonlib.read(resp.body)

postIdentica = postIdenticaPassword

# from http://drewp.quickwitretort.com/2010/09/13/0
def makeOauthFilter(graph, subj):
    rows = graph.queryd("""
    SELECT ?ck ?cs ?t ?ts WHERE {
      ?id foaf:holdsAccount [
          a mb:TwitterAccount ;
          mb:oauthConsumerKey ?ck ;
          mb:oauthConsumerSecret ?cs ;
          mb:oauthToken ?t ;
          mb:oauthTokenSecret ?ts
      ] .
    }
    """, initBindings={'id' : subj})
    conf = rows[0]
    consumer = restkit.util.oauth2.Consumer(conf['ck'], conf['cs'])
    token = restkit.util.oauth2.Token(conf['t'], conf['ts'])
    return restkit.filters.oauth2.OAuthFilter("*", consumer, token,
              restkit.util.oauth2.SignatureMethod_HMAC_SHA1())

def postTwitter(graph, openid, msg):
    """
    openid is an RDF node that foaf:holdsAccount which is a mb:TwitterAccount
    """
    oauthFilter = makeOauthFilter(graph, openid)
    resp = restkit.request(
        method="POST",
        url="http://api.twitter.com/1/statuses/update.json",
        filters=[oauthFilter],
        body={'status' : msg})
    if resp.status_int != 200:
        raise ValueError("%s: %s" % (resp.status, resp.body_string()))

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
    graph = RemoteSparql('http://bang:8080/openrdf-sesame/repositories', 'cmd',
                         dict(foaf=FOAF, mb=MB))
    drewp = URIRef("http://bigasterisk.com/foaf.rdf#drewp")
    if 1:

        #postIdentica(graph, drewp, 'test')
        postTwitter(graph, drewp, 'test')
    else:
        print postIdenticaPassword(graph, drewp, "(testing new post library)")
