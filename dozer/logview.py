import collections
import itertools
import logging
import os
import re
import sys
import time
import traceback

from mako.lookup import TemplateLookup
from webob import Request

from dozer.util import asbool

try:
    import thread
except ImportError:
    # Python 3.x
    try:
        import _thread as thread
    except ImportError:
        # I've no idea.  Maybe Jython?
        thread = None

try:
    unicode
except NameError:
    # Python 3.x
    unicode = str


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
        if config is None:
            config = {}
        self.app = app
        tmpl_dir = os.path.join(here_dir, 'templates')
        self.mako = TemplateLookup(directories=[tmpl_dir],
                                   default_filters=['h'])

        self.log_colors = {}
        for key, val in itertools.chain(iter(config.items()),
                                        iter(kwargs.items())):
            if key.startswith('logview.'):
                self.log_colors[key[len('logview.'):]] = val

        self.traceback_colors = {}
        for key, val in itertools.chain(iter(config.items()),
                                        iter(kwargs.items())):
            if key.startswith('traceback.'):
                self.traceback_colors[key[len('traceback.'):]] = val

        self.logger = logging.getLogger(__name__)
        self.loglevel = getattr(logging, loglevel)

        self.keep_tracebacks = asbool(kwargs.get(
            'keep_tracebacks', config.get(
                'keep_tracebacks', RequestHandler.keep_tracebacks)))
        self.keep_tracebacks_limit = int(kwargs.get(
            'keep_tracebacks_limit', config.get(
                'keep_tracebacks_limit', RequestHandler.keep_tracebacks_limit)))
        self.skip_first_n_frames = int(kwargs.get(
            'skip_first_n_frames', config.get(
                'skip_first_n_frames', RequestHandler.skip_first_n_frames)))
        self.skip_last_n_frames = int(kwargs.get(
            'skip_last_n_frames', config.get(
                'skip_last_n_frames', RequestHandler.skip_last_n_frames)))
        self.stack_formatter = kwargs.get(
            'stack_formatter', config.get(
                'stack_formatter', RequestHandler.stack_formatter))
        self.tb_formatter = kwargs.get(
            'tb_formatter', config.get(
                'tb_formatter', RequestHandler.tb_formatter))

        reqhandler = RequestHandler()
        reqhandler.setLevel(self.loglevel)
        reqhandler.keep_tracebacks = self.keep_tracebacks
        reqhandler.keep_tracebacks_limit = self.keep_tracebacks_limit
        reqhandler.skip_first_n_frames = self.skip_first_n_frames
        reqhandler.skip_last_n_frames = self.skip_last_n_frames
        if self.stack_formatter:
            reqhandler.stack_formatter = self._resolve(self.stack_formatter)
        if self.tb_formatter:
            reqhandler.tb_formatter = self._resolve(self.tb_formatter)
        logging.getLogger('').addHandler(reqhandler)
        self.reqhandler = reqhandler

    def _resolve(self, dotted_name):
        if isinstance(dotted_name, collections.Callable):
            # let's let people supply the function directly
            return dotted_name
        modname, fn = dotted_name.rsplit('.', 1)
        mod = __import__(modname, {}, {}, ['*'])
        return getattr(mod, fn)

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
                                 logcolors=self.log_colors,
                                 traceback_colors=self.traceback_colors,
                                 tottime=tottime, start=start)
            logbar = logbar.encode('ascii', 'xmlcharrefreplace')
            response.body = self.splice(response.body, logbar)
        return response(environ, start_response)

    def splice(self, body, logbar):
        assert isinstance(body, bytes)
        assert isinstance(logbar, bytes)
        parts = re.split(b'(<body[^>]*>)', body, 1)
        # parts = ['preamble', '<body ...>', 'text'] or just ['text']
        # we want to insert our logbar after <body> (if it exists) and
        # in front of text
        return b''.join(parts[:-1] + [logbar] + parts[-1:])

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
    keep_tracebacks_limit = 0
    skip_first_n_frames = 0
    skip_last_n_frames = 6 # number of frames beween logger.log() and our emit()
                           # determined empirically on Python 2.6
    stack_formatter = None # 'package.module.function'
                           # e.g. 'traceback.format_stack'
                           # note: disables skip_first_n_frames
    tb_formatter = None    # 'package.module.function'
                           # e.g. 'traceback.format_tb'

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
        if self.keep_tracebacks and (not self.keep_tracebacks_limit or
                len(self.buffer[record.thread]) < self.keep_tracebacks_limit):
            f = sys._getframe(self.skip_last_n_frames)
            if self.stack_formatter:
                record.traceback = self.stack_formatter(f)
            else:
                record.traceback = traceback.format_list(
                    traceback.extract_stack(f)[self.skip_first_n_frames:])
        if record.exc_info and record.exc_info != (None, None, None):
            # When you do log.exception() when there's no exception, you get
            # record.exc_info == (None, None, None)
            exc_type, exc_value, exc_tb = record.exc_info
            if self.tb_formatter:
                record.exc_traceback = self.tb_formatter(exc_tb)
            else:
                record.exc_traceback = traceback.format_tb(exc_tb)
        # Make sure we interpolate the message early.  Consider this code:
        #    a_list = [1, 2, 3]
        #    log.debug('a_list = %r', a_list)
        #    del a_list[:]
        # if we call getMessage() only when we're rendering all the messages
        # at the end of request processing, we will see `a_list = []` instead
        # of `a_list = [1, 2, 3]`
        record.full_message = record.getMessage()

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
