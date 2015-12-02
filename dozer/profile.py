import errno
import os
import re
import time
from datetime import datetime

try:
    import cPickle
except ImportError:
    # Python 3.x
    import pickle as cPickle

try:
    import cProfile
except ImportError:
    # Python 3.x
    import profile as cProfile

try:
    import thread
except ImportError:
    # Python 3.x
    import _thread as thread

from pkg_resources import resource_filename
from mako.lookup import TemplateLookup
from webob import Request, Response
from webob import exc, static


here_dir = os.path.dirname(os.path.abspath(__file__))

DEFAULT_IGNORED_PATHS = [r'/favicon\.ico$', r'^/error/document']


class Profiler(object):
    def __init__(self, app, global_conf=None, profile_path=None,
                 ignored_paths=DEFAULT_IGNORED_PATHS,
                 dot_graph_cutoff=0.2, **kwargs):
        """Profiles an application and saves the pickled version to a
        file
        """
        assert profile_path, "need profile_path"
        assert os.path.isdir(profile_path), "%r: no such directory" % profile_path
        self.app = app
        self.conf = global_conf
        self.dot_graph_cutoff = float(dot_graph_cutoff)
        self.profile_path = profile_path
        self.ignored_paths = list(map(re.compile, ignored_paths))
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
        for regex in self.ignored_paths:
            if regex.match(environ['PATH_INFO']) is not None:
                return self.app(environ, start_response)
        return self.run_profile(environ, start_response)

    def profiler(self, req):
        assert req.path_info_pop() == '_profiler'
        next_part = req.path_info_pop() or 'showall'
        method = getattr(self, next_part, None)
        if method is None:
            return exc.HTTPNotFound('Nothing could be found to match %r' % next_part)
        if not getattr(method, 'exposed', False):
            return exc.HTTPForbidden('Access to %r is forbidden' % next_part)
        return method(req)

    def media(self, req):
        """Static path where images and other files live"""
        path = resource_filename('dozer', 'media')
        app = static.DirectoryApp(path)
        return app
    media.exposed = True

    def show(self, req):
        profile_id = req.path_info_pop()
        if not profile_id:
            return exc.HTTPNotFound('Missing profile id to view')
        dir_name = self.profile_path or ''
        fname = os.path.join(dir_name, profile_id) + '.pkl'
        with open(fname, 'rb') as f:
            data = cPickle.load(f)
        top = [x for x in data['profile'].values() if not x.get('callers')]
        res = Response()
        res.body = self.render('/show_profile.mako', time=data['time'],
                               profile=top, profile_data=data['profile'],
                               environ=data['environ'], id=profile_id)
        return res
    show.exposed = True

    def showall(self, req):
        dir_name = self.profile_path
        profiles = []
        errors = []
        max_cost = 1 # avoid division by zero
        for profile_file in os.listdir(dir_name):
            if profile_file.endswith('.pkl'):
                path = os.path.join(self.profile_path, profile_file)
                modified = os.stat(path).st_mtime
                try:
                    with open(path, 'rb') as f:
                        data = cPickle.load(f)
                except Exception as e:
                    errors.append((modified, '%s: %s' % (e.__class__.__name__, e), profile_file[:-4]))
                else:
                    environ = data['environ']
                    top = [x for x in data['profile'].values() if not x.get('callers')]
                    if top:
                        total_cost = max(float(x['cost']) for x in top)
                    else:
                        total_cost = 0
                    max_cost = max(max_cost, total_cost)
                    profiles.append((modified, environ, total_cost, profile_file[:-4]))

        profiles.sort(reverse=True)
        errors.sort(reverse=True)
        res = Response()
        if profiles:
            earliest = profiles[-1][0]
        else:
            earliest = None
        res.body = self.render('/list_profiles.mako', profiles=profiles,
                               errors=errors, now=time.time(),
                               earliest=earliest, max_cost=max_cost)
        return res
    showall.exposed = True

    def delete(self, req):
        profile_id = req.path_info_pop()
        if profile_id: # this prob a security risk
            try:
                for ext in ('.gv', '.pkl'):
                    os.unlink(os.path.join(self.profile_path, profile_id + ext))
            except OSError as e:
                if e.errno == errno.ENOENT:
                    pass # allow a file not found exception
                else:
                    raise
            return Response('deleted %s' % profile_id)

        for filename in os.listdir(self.profile_path):
            if filename.endswith('.pkl') or filename.endswith('.gv'):
                os.unlink(os.path.join(self.profile_path, filename))
        res = Response()
        res.location = '/_profiler/showall'
        res.status_int = 302
        return res
    delete.exposed = True


    def render(self, name, **vars):
        tmpl = self.mako.get_template(name)
        return tmpl.render(**vars).encode('ascii', 'xmlcharrefreplace')

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
        body = b''.join(response_body)
        results = prof.getstats()
        tree = buildtree(results)

        # Pull out 'safe' bits from environ
        safe_environ = {}
        for k, v in environ.items():
            if k.startswith('HTTP_'):
                safe_environ[k] = v
            elif k in ['REQUEST_METHOD', 'SCRIPT_NAME', 'PATH_INFO',
                       'QUERY_STRING', 'CONTENT_TYPE', 'CONTENT_LENGTH',
                       'SERVER_NAME', 'SERVER_PORT', 'SERVER_PROTOCOL']:
                safe_environ[k] = v
        safe_environ['thread_id'] = str(thread.get_ident())
        profile_run = dict(time=datetime.now(), profile=tree,
                           environ=safe_environ)
        dir_name = self.profile_path or ''

        openflags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_BINARY', 0)
        while True:
            fname_base = str(time.time()).replace('.', '_')
            prof_file = fname_base + '.pkl'
            try:
                fd = os.open(os.path.join(dir_name, prof_file), openflags)
            except OSError as e:
                if e.errno == errno.EEXIST:
                    # file already exists, try again with a slightly different
                    # timestamp hopefully
                    pass
                else:
                    raise
            else:
                break

        with os.fdopen(fd, 'wb') as f:
            cPickle.dump(profile_run, f)
        write_dot_graph(results, tree, os.path.join(dir_name, fname_base+'.gv'),
                        cutoff=self.dot_graph_cutoff)
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


def graphlabel(code):
    lb = label(code)
    return lb.replace('"', "'").strip()


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

def color(w):
    # color scheme borrowed from
    # http://gprof2dot.jrfonseca.googlecode.com/hg/gprof2dot.py
    hmin, smin, lmin = 2/3., 0.8, .25
    hmax, smax, lmax = 0, 1, .5
    gamma = 2.2
    h = hmin + w * (hmax - hmin)
    s = smin + w * (smax - smin)
    l = lmin + w * (lmax - lmin)
    # http://www.w3.org/TR/css3-color/#hsl-color
    if l <= 0.5:
        m2 = l * (s + 1)
    else: # pragma: nocover -- because our lmax is <= .5!
        m2 = l + s - l * s
    m1 = l * 2 - m2
    def h2rgb(m1, m2, h):
        if h < 0:
            h += 1.0
        elif h > 1: # pragma: nocover -- our hmax is 2/3, and we add 1/3 to that
            h -= 1.0
        if h * 6 < 1.0:
            return m1 + (m2 - m1) * h * 6
        elif h * 2 < 1:
            return m2
        elif h * 3 < 2:
            return m1 + (m2 - m1) * (2/3.0 - h) * 6
        else:
            return m1
    r = h2rgb(m1, m2, h + 1/3.0)
    g = h2rgb(m1, m2, h)
    b = h2rgb(m1, m2, h - 1/3.0)
    # gamma correction
    r **= gamma
    g **= gamma
    b **= gamma
    # graphvizification
    r = min(max(0, round(r * 0xff)), 0xff)
    g = min(max(0, round(g * 0xff)), 0xff)
    b = min(max(0, round(b * 0xff)), 0xff)
    return "#%02X%02X%02X" % (r, g, b)


def write_dot_graph(data, tree, filename, cutoff=0.2):
    f = open(filename, 'w')
    f.write('digraph prof {\n')
    f.write('\tsize="11,9"; ratio = fill;\n')
    f.write('\tnode [style=filled];\n')

    # Find the largest time
    highest = 0.00
    for entry in tree.values():
        if float(entry['cost']) > highest:
            highest = float(entry['cost'])
    if highest == 0:
        highest = 1 # avoid division by zero

    for entry in data:
        code = entry.code
        entry_name = graphlabel(code)
        skip = float(setup_time(entry.totaltime)) < cutoff
        if isinstance(code, str) or skip:
            continue
        else:
            t = tree[label(code)]['cost']
            c = color(float(t) / highest)
            f.write('\t"%s" [label="%s\\n%sms",color="%s",fontcolor="white"]\n' % (entry_name, code.co_name, t, c))
        if entry.calls:
            for subentry in entry.calls:
                subcode = subentry.code
                skip = float(setup_time(subentry.totaltime)) < cutoff
                if isinstance(subcode, str) or skip:
                    continue
                sub_name = graphlabel(subcode)
                f.write('\t"%s" -> "%s" [label="%s"]\n' % \
                    (entry_name, sub_name, subentry.callcount))
    f.write('}\n')
    f.close()


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
        node['cost'] = setup_time(entry.totaltime)
        node['function'] = label(code)

        if entry.calls:
            for subentry in entry.calls:
                subnode = {}
                subnode['builtin'] = isinstance(subentry.code, str)
                subnode['cost'] = setup_time(subentry.totaltime)
                subnode['function'] = label(subentry.code)
                subnode['callcount'] = subentry.callcount
                node.setdefault('calls', []).append(subnode)
                callregistry.setdefault(subnode['function'], []).append(node['function'])
        else:
            node['calls'] = []
        functree[node['function']] = node
    for key in callregistry:
        node = functree[key]
        node['callers'] = callregistry[key]
    return functree
