import logging
import os
import re
import time

from mako.lookup import TemplateLookup
from paste import urlparser
from webob import Request, Response
from webob import exc

try:
    import thread
    import threading
except ImportError:
    thread = None


here_dir = os.path.dirname(os.path.abspath(__file__))


class Logview(object):
    def __init__(self, app, config=None, loglevel='DEBUG', **kwargs):
        """Stores logging statements per request, and includes a bar on
        the page that shows the logging statements
        
        ''loglevel''
            Default log level for messages that should be caught.

        Config can contain optional additional loggers and the colors
        they should be highlighted (in an ini file)::
            
            logview.sqlalchemy = #ff0000

        Or if passing a dict::
            
            app = Logview(app, {'logview.sqlalchemy':'#ff0000'})

        """
        self.app = app
        tmpl_dir = os.path.join(here_dir, 'templates')
        self.mako = TemplateLookup(directories=[tmpl_dir])
        
        self.log_colors = {}
        for key, val in config.iteritems():
            if key.startswith('logview.'):
                self.log_colors[key[8:]] = val
        
        reqhandler = RequestHandler()
        reqhandler.setLevel(getattr(logging, loglevel))
        logging.getLogger('').addHandler(reqhandler)
        self.reqhandler = reqhandler

    def __call__(self, environ, start_response):
        if thread:
            tok = thread.get_ident()
        else:
            tok = None
        
        req = Request(environ)
        req.base_path = req.application_url + '/_logview'
        if req.path_info_peek() == '_logview':
            return self.logview(req)(environ, start_response)
        start = time.time()
        response = req.get_response(self.app)
        tottime = time.time() - start
        reqlogs = self.reqhandler.pop_events(tok)
        if response.headers['content-type'].startswith('text/html'):
            logbar = self.render('/logbar.mako', events=reqlogs, 
                                 logcolors = self.log_colors, tottime=tottime)
            response.body = response.body.replace('<body>',
                                                  '<body>%s' % logbar)
        return response(environ, start_response)

    def logview(self, req):
        assert req.path_info_pop() == '_logivew'
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

    def render(self, name, **vars):
        tmpl = self.mako.get_template(name)
        return tmpl.render(**vars)


class RequestHandler(logging.Handler):
    """
    A handler class which only records events if its set as active for
    a given thread/process (request). Log history per thread must be
    removed manually, preferably at the end of the request. A reference
    to the RequestHandler instance should be retained for this access.

    This handler otherwise works identically to a request-handler,
    except that events are logged to specific 'channels' based on
    thread id when available.

    """
    def __init__(self):
        """Initialize the handler."""
        logging.Handler.__init__(self)
        self.buffer = {}

    def emit(self, record):
        """Emit a record.

        Append the record. If shouldFlush() tells us to, call flush() to process
        the buffer.
        """ 
        self.buffer.setdefault(record.thread, []).append(record)

    def pop_events(self, thread_id):
        """Return all the events logged for particular thread"""
        if thread_id in self.buffer:
            return self.buffer.pop(thread_id)
        else:
            return []

    def flush(self):
        """Kills all data in the buffer"""
        for key in self.buffer:
            del self.buffer[key]
    
    def close(self):
        """Close the handler.

        This version just flushes and chains to the parent class' close().
        """
        self.flush()
        logging.Handler.close(self)
