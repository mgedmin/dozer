import cProfile
import cPickle
import time
import os
from datetime import datetime
from pkg_resources import resource_filename

from mako.lookup import TemplateLookup
from paste import urlparser
from webob import Request, Response
from webob import exc

here_dir = os.path.dirname(os.path.abspath(__file__))

class Profiler(object):
    def __init__(self, app, global_conf=None, profile_path=None, **kwargs):
        """Profiles an application and saves the pickled version to a
        file
        """
        self.app = app
        self.conf = global_conf
        self.profile_path = profile_path
        tmpl_dir = os.path.join(here_dir, 'templates')
        self.mako = TemplateLookup(directories=[tmpl_dir])
    
    def __call__(self, environ, start_response):
        assert not environ['wsgi.multiprocess'], (
            "Dozer middleware is not usable in a "
            "multi-process environment")
        req = Request(environ)
        req.base_path = req.application_url + '/_profiler'
        if req.path_info_peek() == '_profiler':
            return self.profiler(req)(environ, start_response)
        elif not environ['PATH_INFO'].startswith('/error/document') and \
            not environ['PATH_INFO'].startswith('/favicon.ico'):
            return self.run_profile(environ, start_response)
        else:
            return self.app(environ, start_response)
    
    def profiler(self, req):
        assert req.path_info_pop() == '_profiler'
        next_part = req.path_info_pop()
        method = getattr(self, next_part, None)
        if method is None:
            return exc.HTTPNotFound('Nothing could be found to match %r' % next_part)
        if not getattr(method, 'exposed', False):
            return exc.HTTPForbidden('Access to %r is forbidden' % next_part)
        return method(req)
    
    def media(self, req):
        """Static path where images and other files live"""
        path = resource_filename('dozer', 'media')
        app = urlparser.StaticURLParser(path)
        return app
    media.exposed = True
    
    def show(self, req):
        profile_id = req.path_info_pop()
        if not profile_id:
            return exc.HTTPNotFound('Missing profile id to view')
        dir_name = self.profile_path or ''
        fname = os.path.join(dir_name, profile_id) + '.pkl'
        data = cPickle.load(open(fname, 'rb'))
        top = [x for x in data['profile'].values() if not x.get('callers')]
        res = Response()
        res.body = self.render('/show_profile.mako', time=data['time'],
                               profile=top, profile_data=data['profile'],
                               environ=data['environ'], id=profile_id)
        return res
    show.exposed = True

    def render(self, name, **vars):
        tmpl = self.mako.get_template(name)
        return tmpl.render(**vars)
    
    def run_profile(self, environ, start_response):
        """Run the profile over the request and save it"""
        prof = cProfile.Profile()
        response_body = []

        def catching_start_response(status, headers, exc_info=None):
            start_response(status, headers, exc_info)
            return response_body.append

        def runapp():
            appiter = self.app(environ, catching_start_response)
            try:
                response_body.extend(appiter)
            finally:
                if hasattr(appiter, 'close'):
                    appiter.close()

        prof.runcall(runapp)
        body = ''.join(response_body)
        results = prof.getstats()
        tree = buildtree(results)
        
        # Pull out 'safe' bits from environ
        safe_environ = {}
        for k, v in environ.iteritems():
            if k.startswith('HTTP_'):
                safe_environ[k] = v
            elif k in ['REQUEST_METHOD', 'SCRIPT_NAME', 'PATH_INFO',
                       'QUERY_STRING', 'CONTENT_TYPE', 'CONTENT_LENGTH',
                       'SERVER_NAME', 'SERVER_PORT', 'SERVER_PROTOCOL']:
                safe_environ[k] = v
        profile_run = dict(time=datetime.now(), profile=tree,
                           environ=safe_environ)
        fname = str(time.time()).replace('.', '_') + '.pkl'
        
        dir_name = self.profile_path or ''
        cPickle.dump(profile_run, open(os.path.join(dir_name, fname), 'wb'))
        del results, tree, profile_run
        return [body]


def label(code):
    """Generate a friendlier version of the code function called"""
    if isinstance(code, str):
        return code
    else:
        return '%s %s:%d' % (code.co_name,
                             code.co_filename,
                             code.co_firstlineno)


def setup_time(t):
    """Takes a time generally assumed to be quite small and blows it
    up into millisecond time.
    
    For example:
        0.004 seconds     -> 4 ms
        0.00025 seconds   -> 0.25 ms
    
    The result is returned as a string.
    
    """
    t = t*1000
    t = '%0.2f' % t
    return t

def buildtree(data):
    """Takes a pmstats object as returned by cProfile and constructs
    a call tree out of it"""
    functree = {}
    callregistry = {}
    for entry in data:
        node = {}
        code = entry.code
        # If its a builtin
        if isinstance(code, str):
            node['filename'] = '~'
            node['source_position'] = 0
            node['func_name'] = code
        else:
            node['filename'] = code.co_filename
            node['source_position'] = code.co_firstlineno
            node['func_name'] = code.co_name
            node['line_no'] = code.co_firstlineno
        node['cost'] = setup_time(entry.inlinetime)
        node['function'] = label(code)
        
        if entry.calls:
            start = entry.inlinetime
            for subentry in entry.calls:
                subnode = {}
                subnode['builtin'] = isinstance(subentry.code, str)
                subnode['cost'] = setup_time(subentry.totaltime)
                subnode['function'] = label(subentry.code)
                subnode['callcount'] = subentry.callcount
                node.setdefault('calls', []).append(subnode)
                callregistry.setdefault(subnode['function'], []).append(node['function'])
                start += subentry.totaltime
            node['cost'] = setup_time(start)
        else:
            node['calls'] = []
        functree[node['function']] = node
    for key in callregistry:
        node = functree[key]
        node['callers'] = callregistry[key]
    return functree
