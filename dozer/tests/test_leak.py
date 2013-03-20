import unittest

from webob import Request
from webtest import TestApp

from dozer.leak import Dozer
from dozer.leak import ReferrerTree
from dozer.leak import url


class DozerForTests(Dozer):
    def __init__(self, app=None, *args, **kw):
        super(DozerForTests, self).__init__(app, *args, **kw)
    def _start_thread(self):
        pass
    def _maybe_warn_about_PIL(self):
        pass


class EvilProxyClass(object):

    some_constant = object()

    def __init__(self, obj):
        self.obj = obj

    @property
    def __module__(self):
        return self.obj.__module__

    @property
    def __name__(self):
        return self.obj.__name__


class TestDozer(unittest.TestCase):

    def make_request(self, subpath='/', base_path='/_dozer'):
        req = Request(dict(PATH_INFO=subpath))
        req.base_path = base_path
        return req

    def test_url(self):
        req = self.make_request('/somewhere')
        self.assertEqual(url(req, 'foo'), '/_dozer/foo')
        self.assertEqual(url(req, '/foo'), '/_dozer/foo')
        req = self.make_request('/somewhere', base_path='/_dozer/')
        self.assertEqual(url(req, 'bar'), '/_dozer/bar')
        self.assertEqual(url(req, '/bar'), '/_dozer/bar')

    def test_tick_handles_types_with_broken_module(self):
        # https://bitbucket.org/bbangert/dozer/issue/3/cannot-user-operator-between-property-and
        dozer = DozerForTests()
        evil_proxy = EvilProxyClass(object) # keep a reference to it
        dozer.tick()

    def test_trace_all_handles_types_with_broken_module(self):
        dozer = DozerForTests()
        evil_proxy = EvilProxyClass(object) # keep a reference to it
        dozer.trace_all(None, 'no-such-module.No-Such-Type')

    def test_trace_one_handles_types_with_broken_module(self):
        dozer = DozerForTests()
        evil_proxy = EvilProxyClass(object) # keep a reference to it
        dozer.trace_one(None, 'no-such-module.No-Such-Type', id(evil_proxy))

    def test_tree_handles_types_with_broken_module(self):
        dozer = DozerForTests()
        evil_proxy = EvilProxyClass(object) # keep a reference to it
        req = self.make_request('/nosuchtype/%d' % id(evil_proxy))
        dozer.tree(req)


class TestReferrerTree(unittest.TestCase):

    def test_get_repr_handles_types_with_broken_module(self):
        req = Request(dict(PATH_INFO='/whatevs'))
        req.base_path = '/_dozer'
        tree = ReferrerTree(None, req)
        evil_proxy = EvilProxyClass(object)
        tree.get_repr(evil_proxy)

    def test_gen_handles_types_with_broken_module(self):
        req = Request({'PATH_INFO': '/whatevs', 'wsgi.url_scheme': 'http',
                       'HTTP_HOST': 'localhost'})
        req.base_path = '/_dozer'
        tree = ReferrerTree(None, req)
        tree.maxdepth = 10
        tree.seen = {}
        list(tree._gen(EvilProxyClass.some_constant))


def hello_world(environ, start_response):
    body = 'hello, world!'
    headers = [('Content-Type', 'text/html; charset=utf8'),
               ('Content-Length', str(len(body)))]
    start_response('200 Ok', headers)
    return [body]


class TestEntireStack(unittest.TestCase):

    def make_wsgi_app(self):
        app = DozerForTests(hello_world)
        app.history['mymodule.MyType'] = [1, 2, 3, 4, 5]
        return app

    def make_test_app(self):
        return TestApp(self.make_wsgi_app())

    def test_application_pass_through(self):
        app = self.make_test_app()
        resp = app.get('/')
        self.assertTrue('hello, world!' in resp)

    def test_dozer_index(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/index')
        self.assertEqual(resp.status_int, 200)
        self.assertTrue('<div id="output">' in resp)

    def test_dozer_chart(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/chart/mymodule.MyType')
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.content_type, 'image/png')

    def test_dozer_trace_all(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/trace/mymodule.MyType')
        self.assertEqual(resp.status_int, 200)
        self.assertTrue('<div id="output">' in resp)

    def test_dozer_trace_one(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/trace/mymodule.MyType/1234')
        self.assertEqual(resp.status_int, 200)
        self.assertTrue('<div id="output">' in resp)

    def test_dozer_tree(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/tree/mymodule.MyType/1234')
        self.assertEqual(resp.status_int, 200)
        self.assertTrue('<div id="output">' in resp)

    def test_dozer_media(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/media/css/main.css')
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.content_type, 'text/css')
        self.assertTrue('.typename {' in resp)

    def test_dozer_not_found(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/nosuchpage', status=404)

    def test_dozer_forbidden(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/dowse', status=403)

