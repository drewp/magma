#!../buildout_bin/python
"""
controls for one supervisor service, log display, shell cmdline
that you can try yourself

http://bigasterisk.com/supervisor/{host}/{service}/
                                        ^^^^^^^^^^^^^
                                        we receive this part
"""
import sys, cyclone.web, socket, json, xmlrpclib, pwd, time
from twisted.internet import reactor

try:
    sys.path.append("/my/proj/homeauto/lib")
    from cycloneerr import PrettyErrorHandler
except ImportError:
    class PrettyErrorHandler(object):
        pass

from twisted.web import xmlrpc
from twisted.internet.defer import inlineCallbacks
import tailer

import supervisor.options
supervisorOptions = supervisor.options.ServerOptions()
supervisorOptions.realize(args=['-c', '/etc/supervisord.conf'])

supervisor = xmlrpc.Proxy('http://localhost:9001/RPC2')

class Status(PrettyErrorHandler, cyclone.web.RequestHandler):
    @inlineCallbacks
    def get(self, service):
        t1 = time.time()
        result = yield supervisor.callRemote(
            'supervisor.getProcessInfo', service)
        print "getProcessInfo in %.3f" % (time.time() - t1)
        out = {
            'host': socket.gethostname(),
            'processInfo': result,
            'log': {
            },
        }
        t1 = time.time()
        # supervisor also has xmlrpc and modules for this
        for chan in ['stdout', 'stderr']:
            try:
                out['log'][chan + 'Tail'] = tailer.tail(
                    open(result[chan + '_logfile']), 20)
            except IOError as e:
                out['log'][chan + 'Tail'] = [repr(e)]

        print "log tails in %.3f" % (time.time() - t1)
        self.write(out)

class Config(PrettyErrorHandler, cyclone.web.RequestHandler):
    def get(self, service):
        pg = [conf for conf in supervisorOptions.process_group_configs
              if conf.name == service][0]
        out = dict([(k, getattr(pg.process_configs[0], k)) for k in [
            'autostart',
            'command',
            'directory',
            'environment',
            'exitcodes',
            'killasgroup',
            'priority',
            'redirect_stderr',
            'startretries',
            'startsecs',
            'stderr_capture_maxbytes',
            'stderr_events_enabled',
            'stdout_capture_maxbytes',
            'stdout_events_enabled',
            'stopasgroup',
            'stopsignal',
            'stopwaitsecs',
            'uid',
            'umask',
            ]])

        out['user'] = pwd.getpwuid(out['uid'])[0]
        self.write(out)

class ProcessCommand(PrettyErrorHandler, cyclone.web.RequestHandler):
    @inlineCallbacks
    def post(self, service):
        req = json.loads(self.request.body)
        if req['cmd'] not in ['startProcess', 'stopProcess']:
            raise NotImplementedError(req['cmd'])
        try:
            result = yield supervisor.callRemote(
                'supervisor.%s' % str(req['cmd']), service)
        except xmlrpclib.Fault as e:
            result = {'fault': str(e)}
        print repr(result)
        if isinstance(result, bool):
            result = {'result' : result}
        self.write(result)

class Services(PrettyErrorHandler, cyclone.web.RequestHandler):
    @inlineCallbacks
    def get(self):
        result = yield supervisor.callRemote('supervisor.getAllProcessInfo')
        self.write({
            'host': socket.gethostname(),
            'services': result,
            })
        
if __name__ == '__main__':
    from twisted.python.log import startLogging
    startLogging(sys.stderr)
    reactor.listenTCP(10004, cyclone.web.Application([
        (r"/(|gui.js|style.css|allservices.html|service.html)", cyclone.web.StaticFileHandler,
         {"path": ".", "default_filename": "supdebug.html"}),
        (r"/.[^/]+/(|gui.js|style.css|service.html)", cyclone.web.StaticFileHandler,
         {"path": ".", "default_filename": "supdebug.html"}),
        (r'/services', Services),
        (r'/(.[^/]+)/status', Status),
        (r'/(.[^/]+)/config', Config),
        (r'/(.[^/]+)/processCommand', ProcessCommand),

        ]))
    reactor.run()
