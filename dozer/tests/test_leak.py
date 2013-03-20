import unittest

from webob import Request

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

