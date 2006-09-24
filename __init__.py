import cgi
import gc
import os
localDir = os.path.join(os.getcwd(), os.path.dirname(__file__))
from StringIO import StringIO
import sys
import threading
import time

import Image
import ImageDraw

import cherrypy
from cherrypy import tools


class _(object): pass
dictproxy = type(_.__dict__)
method_types = [type(tuple.__le__),                 # 'wrapper_descriptor'
                type([1].__le__),                   # 'method-wrapper'
                type(sys.getcheckinterval),         # 'builtin_function_or_method'
                type(cgi.FieldStorage.getfirst),    # 'instancemethod'
                ]

def template(name, **params):
    p = {'maincss': cherrypy.url("/main.css"),
         'home': cherrypy.url("/"),
         }
    p.update(params)
    return open(os.path.join(localDir, name)).read() % p


class Root:
    
    period = 5
    maxhistory = 300
    
    def __init__(self):
        self.history = {}
        self.samples = 0
        self.runthread = threading.Thread(target=self.start)
        self.runthread.start()
    
    def start(self):
        self.running = True
        while self.running:
            self.tick()
            time.sleep(self.period)
    
    def tick(self):
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
    
    main_css = tools.staticfile.handler(filename=os.path.join(localDir, "main.css"))
    
    def index(self, floor=0):
        rows = []
        for typename, hist in self.history.iteritems():
            maxhist = max(hist)
            if maxhist > int(floor):
                row = ('<div class="typecount">%s<br />'
                       '<img class="chart" src="%s" /><br />'
                       'Min: %s Cur: %s Max: %s <a href="%s">TRACE</a></div>'
                       % (cgi.escape(typename),
                          cherrypy.url("chart/%s" % typename),
                          min(hist), hist[-1], maxhist,
                          cherrypy.url("trace/%s" % typename),
                          )
                       )
                rows.append(row)
        return template("graphs.html", output="\n".join(rows))
    index.exposed = True
    
    def chart(self, typename):
        """Return a sparkline chart of the given type."""
        data = self.history[typename]
        height = 20.0
        scale = height / max(data)
        im = Image.new("RGB", (len(data), height), 'white')
        draw = ImageDraw.Draw(im)
        draw.line([(i, int(height - (v * scale))) for i, v in enumerate(data)],
                  fill="#009900")
        del draw
        
        f = StringIO()
        im.save(f, "PNG")
        result = f.getvalue()
        
        cherrypy.response.headers["Content-Type"] = "image/png"
        return result
    chart.exposed = True
    
    def trace(self, typename, objid=None):
        gc.collect()
        rows = []
        if objid is None:
            for obj in gc.get_objects():
                objtype = type(obj)
                if objtype.__module__ + "." + objtype.__name__ == typename:
                    rows.append(self.tracelink(obj))
            if not rows:
                rows = ["<h3>The type you requested was not found.</h3>"]
        else:
            objid = int(objid)
            for obj in gc.get_objects():
                if id(obj) == objid:
                    objtype = type(obj)
                    if objtype.__module__ + "." + objtype.__name__ != typename:
                        rows = ["<h3>The object you requested is no longer "
                                "of the correct type.</h3>"]
                    else:
                        rows.append('<p>%s</p>' % self.get_repr(obj, 2500))
                        
                        # Attributes
                        rows.append('<div class="obj"><h3>Attributes</h3>')
                        for k in dir(obj):
                            v = getattr(obj, k)
                            if type(v) not in method_types:
                                rows.append('<p class="attr"><b>%s:</b> %s</p>' %
                                            (k, self.get_repr(v)))
                        rows.append('</div>')
                        
                        # Referrers
                        rows.append('<div class="obj"><h3>Referrers (Parents)</h3>')
                        loc = locals()
                        frame = sys._getframe()
                        for parent in gc.get_referrers(obj):
                            if parent is loc or parent is frame:
                                continue
                            
                            rows.append('<div class="parent">')
                            
                            # Show parent
                            rows.append(self.tracelink(parent))
                            
                            # Show grandparent if this parent is a __dict__
                            if type(parent) in (dict, dictproxy):
                                for gparent in gc.get_referrers(parent):
                                    if getattr(gparent, "__dict__", None) is parent:
                                        rows.append(self.tracelink(gparent, "gparent"))
                                        break
                            
                            rows.append('</div>')
                        rows.append('</div>')
                        
                        # Referents
                        rows.append('<div class="obj"><h3>Referents (Children)</h3>')
                        for child in gc.get_referents(obj):
                            rows.append(self.tracelink(child))
                        rows.append('</div>')
                    break
            if not rows:
                rows = ["<h3>The object you requested was not found.</h3>"]
        
        params = {'output': "\n".join(rows),
                  'typename': cgi.escape(typename),
                  'objid': '',
                  }
        if objid is not None:
            params['objid'] = str(objid)
        return template("trace.html", **params)
    trace.exposed = True
    
    def tracelink(self, obj, classname="obj"):
        objtype = type(obj)
        typename = objtype.__module__ + "."
        if typename == "__builtin__.":
            typename = ""
        typename += objtype.__name__
        return ('<p class="%s"><a class="objectid" href="%s">%s</a> '
                '<span class="typename">%s</span><br />'
                '<span class="repr">%s</span></p>'
                % (classname,
                   cherrypy.url("/trace/%s/%s" % (typename, id(obj))),
                   id(obj), typename, self.get_repr(obj))
                )
    
    repr_limit = 250
    
    def get_repr(self, obj, limit=None, escape=True):
        try:
            result = repr(obj)
        except:
            result = "unrepresentable object: %r" % sys.exc_info()[1]
        
        if limit is None:
            limit = self.repr_limit
        
        if len(result) > limit:
            result = result[:limit] + "..."
        
        if escape:
            result = cgi.escape(result)
        
        return result


if __name__ == '__main__':
##    cherrypy.config.update({"environment": "production"})
    root = Root()
    cherrypy.quickstart(root)
