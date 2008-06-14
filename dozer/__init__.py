import cgi
import gc
import os
import sys
import threading
import time
from StringIO import StringIO
from types import FrameType, ModuleType

import Image
import ImageDraw

from paste import fileapp
from paste import urlparser
from pkg_resources import resource_filename
from webob import Request, Response
from webob import exc

import dozer.reftree as reftree

localDir = os.path.join(os.getcwd(), os.path.dirname(__file__))

def get_repr(obj, limit=250):
    return cgi.escape(reftree.get_repr(obj, limit))

class _(object): pass
dictproxy = type(_.__dict__)

method_types = [type(tuple.__le__),                 # 'wrapper_descriptor'
                type([1].__le__),                   # 'method-wrapper'
                type(sys.getcheckinterval),         # 'builtin_function_or_method'
                type(cgi.FieldStorage.getfirst),    # 'instancemethod'
                ]

def url(req, path):
    if path.startswith('/'):
        path = path[1:]
    base_path = req.base_path
    if base_path.endswith('/'):
        return base_path + path
    else:
        return base_path + '/' + path


def template(req, name, **params):
    p = {'maincss': url(req, "/media/main.css"),
         'home': url(req, "/index"),
         }
    p.update(params)
    return open(os.path.join(localDir, 'media', name)).read() % p


class Dozer(object):
    """Sets up a page that displays object information to help
    troubleshoot memory leaks"""
    period = 5
    maxhistory = 300
    
    def __init__(self, app, global_conf=None, media_paths=None, **kwargs):
        self.app = app
        self.media_paths = media_paths or {}
        self.history = {}
        self.samples = 0
        self.runthread = threading.Thread(target=self.start)
        self.runthread.start()
    
    def __call__(self, environ, start_response):
        assert not environ['wsgi.multiprocess'], (
            "Dozer middleware is not usable in a "
            "multi-process environment")
        req = Request(environ)
        req.base_path = req.application_url + '/_dozer'
        if req.path_info_peek() == '_dozer':
            return self.dowse(req)(environ, start_response)
        else:
            return self.app(environ, start_response)
    
    def dowse(self, req):
        assert req.path_info_pop() == '_dozer'
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

    def start(self):
        self.running = True
        while self.running:
            self.tick()
            time.sleep(self.period)
    
    def tick(self):
        gc.collect()
        
        typecounts = {}
        for obj in gc.get_objects():
            objtype = type(obj)
            if objtype in typecounts:
                typecounts[objtype] += 1
            else:
                typecounts[objtype] = 1
        
        for objtype, count in typecounts.iteritems():
            typename = objtype.__module__ + "." + objtype.__name__
            if typename not in self.history:
                self.history[typename] = [0] * self.samples
            self.history[typename].append(count)
        
        samples = self.samples + 1
        
        # Add dummy entries for any types which no longer exist
        for typename, hist in self.history.iteritems():
            diff = samples - len(hist)
            if diff > 0:
                hist.extend([0] * diff)
        
        # Truncate history to self.maxhistory
        if samples > self.maxhistory:
            for typename, hist in self.history.iteritems():
                hist.pop(0)
        else:
            self.samples = samples
    
    def stop(self):
        self.running = False
    
    def index(self, req):
        floor = req.GET.get('floor', 0)
        rows = []
        typenames = self.history.keys()
        typenames.sort()
        for typename in typenames:
            hist = self.history[typename]
            maxhist = max(hist)
            if maxhist > int(floor):
                row = ('<div class="typecount">%s<br />'
                       '<img class="chart" src="%s" /><br />'
                       'Min: %s Cur: %s Max: %s <a href="%s">TRACE</a></div>'
                       % (cgi.escape(typename),
                          url(req, "chart/%s" % typename),
                          min(hist), hist[-1], maxhist,
                          url(req, "trace/%s" % typename),
                          )
                       )
                rows.append(row)
        res = Response()
        res.body = template(req, "graphs.html", output="\n".join(rows))
        return res
    index.exposed = True
    
    def chart(self, req):
        """Return a sparkline chart of the given type."""
        typename = req.path_info_pop()
        data = self.history[typename]
        height = 20.0
        scale = height / max(data)
        im = Image.new("RGB", (len(data), int(height)), 'white')
        draw = ImageDraw.Draw(im)
        draw.line([(i, int(height - (v * scale))) for i, v in enumerate(data)],
                  fill="#009900")
        del draw
        
        f = StringIO()
        im.save(f, "PNG")
        result = f.getvalue()
        
        res = Response()
        res.headers["Content-Type"] = "image/png"
        res.body = result
        return res
    chart.exposed = True
    
    def trace(self, req):
        typename = req.path_info_pop()
        objid = req.path_info_pop()
        gc.collect()
        
        if objid is None:
            rows = self.trace_all(req, typename)
        else:
            rows = self.trace_one(req, typename, objid)
        
        res = Response()
        res.body =template(req, "trace.html", output="\n".join(rows),
                        typename=cgi.escape(typename),
                        objid=str(objid or ''))
        return res
    trace.exposed = True
    
    def trace_all(self, req, typename):
        rows = []
        for obj in gc.get_objects():
            objtype = type(obj)
            if objtype.__module__ + "." + objtype.__name__ == typename:
                rows.append("<p class='obj'>%s</p>"
                            % ReferrerTree(obj, req).get_repr(obj))
        if not rows:
            rows = ["<h3>The type you requested was not found.</h3>"]
        return rows
    
    def trace_one(self, req, typename, objid):
        rows = []
        objid = int(objid)
        all_objs = gc.get_objects()
        for obj in all_objs:
            if id(obj) == objid:
                objtype = type(obj)
                if objtype.__module__ + "." + objtype.__name__ != typename:
                    rows = ["<h3>The object you requested is no longer "
                            "of the correct type.</h3>"]
                else:
                    # Attributes
                    rows.append('<div class="obj"><h3>Attributes</h3>')
                    for k in dir(obj):
                        v = getattr(obj, k)
                        if type(v) not in method_types:
                            rows.append('<p class="attr"><b>%s:</b> %s</p>' %
                                        (k, get_repr(v)))
                        del v
                    rows.append('</div>')
                    
                    # Referrers
                    rows.append('<div class="refs"><h3>Referrers (Parents)</h3>')
                    rows.append('<p class="desc"><a href="%s">Show the '
                                'entire tree</a> of reachable objects</p>'
                                % url(req, "/tree/%s/%s" % (typename, objid)))
                    tree = ReferrerTree(obj, req)
                    tree.ignore(all_objs)
                    for depth, parentid, parentrepr in tree.walk(maxdepth=1):
                        if parentid:
                            rows.append("<p class='obj'>%s</p>" % parentrepr)
                    rows.append('</div>')
                    
                    # Referents
                    rows.append('<div class="refs"><h3>Referents (Children)</h3>')
                    for child in gc.get_referents(obj):
                        rows.append("<p class='obj'>%s</p>" % tree.get_repr(child))
                    rows.append('</div>')
                break
        if not rows:
            rows = ["<h3>The object you requested was not found.</h3>"]
        return rows
    
    def tree(self, req):
        typename = req.path_info_pop()
        objid = req.path_info_pop()
        gc.collect()
        
        rows = []
        objid = int(objid)
        all_objs = gc.get_objects()
        for obj in all_objs:
            if id(obj) == objid:
                objtype = type(obj)
                if objtype.__module__ + "." + objtype.__name__ != typename:
                    rows = ["<h3>The object you requested is no longer "
                            "of the correct type.</h3>"]
                else:
                    rows.append('<div class="obj">')
                    
                    tree = ReferrerTree(obj, req)
                    tree.ignore(all_objs)
                    for depth, parentid, parentrepr in tree.walk(maxresults=1000):
                        rows.append(parentrepr)
                    
                    rows.append('</div>')
                break
        if not rows:
            rows = ["<h3>The object you requested was not found.</h3>"]
        
        params = {'output': "\n".join(rows),
                  'typename': cgi.escape(typename),
                  'objid': str(objid),
                  }
        res = Response()
        res.body = template(req, "tree.html", **params)
        return res
    tree.exposed = True



class ReferrerTree(reftree.Tree):
    
    ignore_modules = True
    
    def _gen(self, obj, depth=0):
        if self.maxdepth and depth >= self.maxdepth:
            yield depth, 0, "---- Max depth reached ----"
            raise StopIteration
        
        if isinstance(obj, ModuleType) and self.ignore_modules:
            raise StopIteration
        
        refs = gc.get_referrers(obj)
        refiter = iter(refs)
        self.ignore(refs, refiter)
        thisfile = sys._getframe().f_code.co_filename
        for ref in refiter:
            # Exclude all frames that are from this module or reftree.
            if (isinstance(ref, FrameType)
                and ref.f_code.co_filename in (thisfile, self.filename)):
                continue
            
            # Exclude all functions and classes from this module or reftree.
            mod = getattr(ref, "__module__", "")
            if "dozer" in mod or "reftree" in mod or mod == '__main__':
                continue
            
            # Exclude all parents in our ignore list.
            if id(ref) in self._ignore:
                continue
            
            # Yield the (depth, id, repr) of our object.
            yield depth, 0, '%s<div class="branch">' % (" " * depth)
            if id(ref) in self.seen:
                yield depth, id(ref), "see %s above" % id(ref)
            else:
                self.seen[id(ref)] = None
                yield depth, id(ref), self.get_repr(ref, obj)
                
                for parent in self._gen(ref, depth + 1):
                    yield parent
            yield depth, 0, '%s</div>' % (" " * depth)
    
    def get_repr(self, obj, referent=None):
        """Return an HTML tree block describing the given object."""
        objtype = type(obj)
        typename = objtype.__module__ + "." + objtype.__name__
        prettytype = typename.replace("__builtin__.", "")
        
        name = getattr(obj, "__name__", "")
        if name:
            prettytype = "%s %r" % (prettytype, name)
        
        key = ""
        if referent:
            key = self.get_refkey(obj, referent)
        return ('<a class="objectid" href="%s">%s</a> '
                '<span class="typename">%s</span>%s<br />'
                '<span class="repr">%s</span>'
                % (url(self.req, "/trace/%s/%s" % (typename, id(obj))),
                   id(obj), prettytype, key, get_repr(obj, 100))
                )
    
    def get_refkey(self, obj, referent):
        """Return the dict key or attribute name of obj which refers to referent."""
        if isinstance(obj, dict):
            for k, v in obj.iteritems():
                if v is referent:
                    return " (via its %r key)" % k
        
        for k in dir(obj) + ['__dict__']:
            if getattr(obj, k, None) is referent:
                return " (via its %r attribute)" % k
        return ""


def dozer_filter_factory(global_conf, **kwargs):
    def filter(app):
        return Dozer(app, global_conf, **kwargs)
    return filter


def dozer_filter_app_factory(app, global_conf, **kwargs):
    return Dozer(app, global_conf, **kwargs)
