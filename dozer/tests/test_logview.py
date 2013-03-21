import unittest
import traceback
import logging

from mock import patch
from webtest import TestApp

from dozer.logview import Logview, RequestHandler


class TestLogview(unittest.TestCase):

    def test_configuration(self):
        logview = Logview(None, config={'logview.foo': 'red',
                                        'traceback.bar': 'green'},
                          stack_formatter=traceback.format_stack,
                          tb_formatter='traceback.format_tb')
        self.assertEqual(logview.log_colors, {'foo': 'red'})
        self.assertEqual(logview.traceback_colors, {'bar': 'green'})
        self.assertEqual(logview.reqhandler.stack_formatter,
                         traceback.format_stack)
        self.assertEqual(logview.reqhandler.tb_formatter, traceback.format_tb)

    def test_splice(self):
        logview = Logview(None)
        testcases = [
            b'[logbar]no body tag',
            b'<html><body>[logbar]text</body></html>',
            b'<html><body class="c">[logbar]text</body></html>',
            b'<html><body>[logbar]text</body><body>haha invalid markup',
        ]
        for expected in testcases:
            orig_body = expected.replace(b'[logbar]', b'')
            self.assertEqual(logview.splice(orig_body, b'[logbar]'), expected)


class TestRequestHandler(unittest.TestCase):

    def test_flush(self):
        handler = RequestHandler()
        handler.buffer[124] = ['pretend record']
        handler.flush()
        self.assertEqual(handler.buffer, {})

    def test_close(self):
        handler = RequestHandler()
        handler.close()


test_log = logging.getLogger(__name__)

def hello_world(environ, start_response):
    path_info = environ['PATH_INFO']
    if path_info == '/image.png':
        content_type = 'image/png'
        body = b'[image data]'
    else:
        content_type = 'text/html; charset=utf-8'
        body = b'hello, world!'
    if path_info == '/error':
        try:
            raise Exception('just testing')
        except Exception:
            test_log.exception('caught exception')
    headers = [('Content-Type', content_type),
               ('Content-Length', str(len(body)))]
    start_response('200 Ok', headers)
    return [body]



class TestEntireStack(unittest.TestCase):

    def make_wsgi_app(self, **kw):
        logview = Logview(hello_world, keep_tracebacks=True, **kw)
        return logview

    def make_test_app(self, **kw):
        return TestApp(self.make_wsgi_app(**kw))

    def test_call(self):
        app = self.make_test_app()
        resp = app.get('/')
        self.assertTrue('hello, world!' in resp)
        self.assertTrue('<div id="DLVlogevents"' in resp)

    def test_call_non_html(self):
        app = self.make_test_app()
        resp = app.get('/image.png')
        self.assertEqual(resp.body, b'[image data]')

    def test_call_without_threading(self):
        app = self.make_test_app()
        with patch('dozer.logview.thread', None):
            app.get('/')

    def test_call_shows_exception_tracebacks(self):
        app = self.make_test_app()
        resp = app.get('/error')
        print(resp) # for debugging
        self.assertTrue('hello, world!' in resp)
        self.assertTrue('<div id="DLVlogevents"' in resp)
        self.assertTrue('caught exception' in resp)
        # we see an exception traceback
        self.assertTrue("raise Exception(&#39;just testing&#39;)" in resp)
        # we see the stack trace that points to the Logger.exception call
        self.assertTrue("test_log.exception(&#39;caught exception&#39;)" in resp)

    def test_custom_formatters(self):
        app = self.make_test_app(stack_formatter=lambda f: '<custom stack>',
                                 tb_formatter=lambda tb: '<custom tb>')
        resp = app.get('/error')
        print(resp) # for debugging
        self.assertTrue('hello, world!' in resp)
        self.assertTrue('<div id="DLVlogevents"' in resp)
        self.assertTrue('caught exception' in resp)
        self.assertTrue("&lt;custom stack&gt;" in resp)
        self.assertTrue("&lt;custom tb&gt;" in resp)
