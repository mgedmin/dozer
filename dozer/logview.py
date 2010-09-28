import logging
import os
import re
import time
import itertools
import traceback
import sys

from mako.lookup import TemplateLookup
from paste import urlparser
from paste.util.converters import asbool
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

            Note: the root logger's log level also matters!  If you do
            logging.getLogger('').setLevel(logging.INFO), no DEBUG messages
            will make it to Logview's handler anyway.

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
        for key, val in itertools.chain(config.iteritems(),
                                        kwargs.iteritems()):
            if key.startswith('logview.'):
                self.log_colors[key[8:]] = val

        self.logger = logging.getLogger(__name__)
        self.loglevel = getattr(logging, loglevel)

        self.keep_tracebacks = asbool(kwargs.get(
            'keep_tracebacks', config.get(
                'keep_tracebacks', RequestHandler.keep_tracebacks)))
        self.keep_tracebacks_limit = int(kwargs.get(
            'keep_tracebacks_limit', config.get(
                'keep_tracebacks_limit', RequestHandler.keep_tracebacks_limit)))
        self.skip_last_n_frames = int(kwargs.get(
            'skip_last_n_frames', config.get(
                'skip_last_n_frames', RequestHandler.skip_last_n_frames)))

        reqhandler = RequestHandler()
        reqhandler.setLevel(self.loglevel)
        reqhandler.keep_tracebacks = self.keep_tracebacks
        reqhandler.keep_tracebacks_limit = self.keep_tracebacks_limit
        reqhandler.skip_last_n_frames = self.skip_last_n_frames
        logging.getLogger('').addHandler(reqhandler)
        self.reqhandler = reqhandler


    def __call__(self, environ, start_response):
        if thread:
            tok = thread.get_ident()
        else:
            tok = None

        req = Request(environ)
        start = time.time()
        self.logger.log(self.loglevel, 'request started')
        response = req.get_response(self.app)
        self.logger.log(self.loglevel, 'request finished')
        tottime = time.time() - start
        reqlogs = self.reqhandler.pop_events(tok)
        if 'content-type' in response.headers and \
           response.headers['content-type'].startswith('text/html'):
            logbar = self.render('/logbar.mako', events=reqlogs,
                                 logcolors=self.log_colors, tottime=tottime,
                                 start=start)
            response.body = re.sub(r'<body([^>]*)>', r'<body\1>%s' % logbar, response.body)
        return response(environ, start_response)

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

    keep_tracebacks = False
    keep_tracebacks_limit = 20 # too many of these make things very very slow
    skip_last_n_frames = 6 # number of frames beween logger.log() and our emit()
                           # determined empirically on Python 2.6

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
        if self.keep_tracebacks:
            if (not self.keep_tracebacks_limit or
                len(self.buffer[record.thread]) < self.keep_tracebacks_limit):
                f = sys._getframe(self.skip_last_n_frames)
                record.traceback = ''.join(traceback.format_stack(f))

    def pop_events(self, thread_id):
        """Return all the events logged for particular thread"""
        if thread_id in self.buffer:
            return self.buffer.pop(thread_id)
        else:
            return []

    def flush(self):
        """Kills all data in the buffer"""
        self.buffer = {}
    
    def close(self):
        """Close the handler.

        This version just flushes and chains to the parent class' close().
        """
        self.flush()
        logging.Handler.close(self)
