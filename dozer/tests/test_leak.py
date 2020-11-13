import gc
import unittest

import webtest
from mock import patch
from webob import Request

from dozer.leak import Dozer
from dozer.leak import ReferrerTree
from dozer.leak import url
from dozer.leak import get_sort_key

from dozer.util import monotonicity


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
    def __module__(self):  # pragma: nocover
        return self.obj.__module__

    @property
    def __name__(self):
        return self.obj.__name__


class MyObj(object):

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return getattr(self, 'name', 'unnamed-MyObj')


class TestDozer(unittest.TestCase):

    def make_request(self, subpath='/', base_path='/_dozer'):
        req = Request(dict(PATH_INFO=subpath))
        req.base_path = base_path
        return req

    def test_get_sortkey(self):
        self.assertEqual((monotonicity, False), get_sort_key("monotonicity"))
        self.assertEqual((monotonicity, True), get_sort_key("-monotonicity"))
        k, rev = get_sort_key("")
        self.assertFalse(rev)
        self.assertIsNone(k)

    def test_url(self):
        req = self.make_request('/somewhere')
        self.assertEqual(url(req, 'foo'), '/_dozer/foo')
        self.assertEqual(url(req, '/foo'), '/_dozer/foo')
        req = self.make_request('/somewhere', base_path='/_dozer/')
        self.assertEqual(url(req, 'bar'), '/_dozer/bar')
        self.assertEqual(url(req, '/bar'), '/_dozer/bar')

    def test_path_normalization(self):
        dozer = DozerForTests(path='/altpath/')
        self.assertEqual(dozer.path, '/altpath')

    def test_start_thread(self):
        with patch('threading.Thread.start'):
            dozer = Dozer(None)
            self.assertEqual(dozer.runthread.name, 'Dozer')
            self.assertTrue(dozer.runthread.daemon)
            # Python 2.x has __target (mangled), Python 3.x has _target
            target = getattr(dozer.runthread, '_Thread__target',
                             getattr(dozer.runthread, '_target', '???'))
            self.assertEqual(target, dozer.start)
            self.assertEqual(dozer.runthread.start.call_count, 1)

    def test_maybe_warn_about_PIL(self):
        with patch('dozer.leak.Dozer._start_thread'):
            with patch('dozer.leak.Image', None):
                with patch('warnings.warn') as warn:
                    dozer = Dozer(None)
                    warn.assert_called_once_with('PIL is not installed, cannot show charts in Dozer')

    def test_start(self):
        with patch('time.sleep') as sleep:
            dozer = DozerForTests()
            dozer.tick = dozer.stop
            dozer.start()
            sleep.assert_called_once_with(dozer.period)

    def test_tick(self):
        dozer = DozerForTests()
        dozer.maxhistory = 10
        for n in range(dozer.maxhistory * 2):
            dozer.tick()

    def test_tick_handles_disappearing_types(self):
        dozer = DozerForTests()
        obj = MyType()
        dozer.tick()
        del obj
        dozer.tick()
        self.assertEqual(dozer.history['mymodule.MyType'], [1, 0])

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

    def test_trace_one_shows_referers(self):
        dozer = DozerForTests()
        a = MyObj(name='the-thing')
        b = MyObj(name='the-referrer', has=a)
        req = self.make_request('/blah/blah')
        rows = dozer.trace_one(req, '{0.__module__}.{0.__name__}'.format(MyObj), id(a))
        self.assertIn('the-referrer', '\n'.join(rows))

    def test_tree_handles_types_with_broken_module(self):
        dozer = DozerForTests()
        evil_proxy = EvilProxyClass(object) # keep a reference to it
        req = self.make_request('/nosuchtype/%d' % id(evil_proxy))
        dozer.tree(req)

    def test_tree_shows_referers(self):
        dozer = DozerForTests()
        a = MyObj(name='the-thing')
        b = MyObj(name='the-referrer', has=a)
        req = self.make_request('/{0.__module__}.{0.__name__}/{1}'.format(type(a), id(a)))
        resp = dozer.tree(req)
        self.assertIn('the-referrer', resp.text)


class TestReferrerTree(unittest.TestCase):

    def make_request(self):
        req = Request({'PATH_INFO': '/whatevs', 'wsgi.url_scheme': 'http',
                       'HTTP_HOST': 'localhost'})
        req.base_path = '/_dozer'
        return req

    def make_tree(self, maxdepth=10):
        req = self.make_request()
        tree = ReferrerTree(None, req)
        tree.maxdepth = maxdepth
        tree.seen = {}
        return tree

    def test_get_repr_handles_types_with_broken_module(self):
        tree = self.make_tree()
        evil_proxy = EvilProxyClass(object)
        tree.get_repr(evil_proxy)

    def test_gen_handles_types_with_broken_module(self):
        tree = self.make_tree()
        list(tree._gen(EvilProxyClass.some_constant))

    def test_gen_skips_itself(self):
        tree = self.make_tree()
        list(tree._gen(ReferrerTree))

    def test_gen_maxdepth(self):
        tree = self.make_tree(maxdepth=1)
        obj = object()
        ref = [obj]
        res = list(tree._gen(obj))
        self.assertIn((1, 0, "---- Max depth reached ----"), res)


def hello_world(environ, start_response):
    body = b'hello, world!'
    headers = [('Content-Type', 'text/html; charset=utf8'),
               ('Content-Length', str(len(body)))]
    start_response('200 Ok', headers)
    return [body]


class MyType(object):
    __module__ = 'mymodule'


class MyFaultyType(object):
    __module__ = 'mymodule'

    foo = 42

    @property
    def bar(self):
        raise KeyError


class TestEntireStack(unittest.TestCase):

    def make_wsgi_app(self):
        dozer = DozerForTests(hello_world)
        dozer.history['mymodule.MyType'] = [1, 2, 3, 4, 5]
        return dozer

    def make_test_app(self):
        return webtest.TestApp(self.make_wsgi_app())

    def test_application_pass_through(self):
        app = self.make_test_app()
        resp = app.get('/')
        self.assertIn('hello, world!', resp)

    def test_dozer(self):
        app = self.make_test_app()
        resp = app.get('/_dozer')
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<div id="output">', resp)

    def test_dozer_index(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/index')
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<div id="output">', resp)

    def test_dozer_chart(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/chart/mymodule.MyType')
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.content_type, 'image/png')

    def test_dozer_chart_no_PIL(self):
        app = self.make_test_app()
        with patch('dozer.leak.Image', None):
            resp = app.get('/_dozer/chart/mymodule.MyType', status=404)

    def test_dozer_trace_all(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/trace/mymodule.MyType')
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<div id="output">', resp)

    def test_dozer_trace_all_not_empty(self):
        app = self.make_test_app()
        obj = MyType() # keep a reference so it's not gc'ed
        resp = app.get('/_dozer/trace/mymodule.MyType')
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<div id="output">', resp)
        self.assertIn("<p class='obj'>", resp)

    def test_dozer_trace_one(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/trace/mymodule.MyType/1234')
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<div id="output">', resp)

    def test_dozer_trace_one_raising_property(self):
        app = self.make_test_app()
        obj = MyFaultyType()  # keep a reference so it's not gc'ed
        resp = app.get('/_dozer/trace/mymodule.MyFaultyType/{}'.format(id(obj)))
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<p class="attr"><b>bar:</b> KeyError()</p>', resp)
        self.assertIn('<p class="attr"><b>foo:</b> 42</p>', resp)

    def test_dozer_trace_one_not_empty(self):
        app = self.make_test_app()
        obj = MyType()
        resp = app.get('/_dozer/trace/mymodule.MyType/%d' % id(obj))
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<div id="output">', resp)
        self.assertIn('<div class="obj">', resp)

    def test_dozer_tree(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/tree/mymodule.MyType/1234')
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<div id="output">', resp)

    def test_dozer_tree_not_empty(self):
        app = self.make_test_app()
        obj = MyType()
        resp = app.get('/_dozer/tree/mymodule.MyType/%d' % id(obj))
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<div id="output">', resp)
        self.assertIn('<div class="obj">', resp)
        # this removes a 3-second pause in the next test
        gc.collect()

    def test_dozer_media(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/media/css/main.css')
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.content_type, 'text/css')
        self.assertIn('.typename {', resp)

    def test_dozer_not_found(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/nosuchpage', status=404)

    def test_dozer_forbidden(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/dowse', status=403)

    def test_dozer_sortby(self):
        app = self.make_test_app()
        app.app.history['mymodule.AnotherType'] = [10, 20, 30, 40, 50]
        resp = app.get('/_dozer/?sortby=-monotonicity')
        self.assertEqual(resp.status_int, 200)

    def test_dozer_floor(self):
        app = self.make_test_app()
        app.app.history['mymodule.AnotherType'] = [10, 20, 30, 40, 50]
        resp = app.get('/_dozer/?floor=4')
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<input name="floor" value="4"/>', resp)
        self.assertIn('mymodule.AnotherType', resp)
        self.assertIn('mymodule.MyType', resp)

        resp = app.get('/_dozer/?floor=10')
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<input name="floor" value="10"/>', resp)
        self.assertIn('mymodule.AnotherType', resp)
        self.assertNotIn('mymodule.MyType', resp)

    def test_dozer_filter(self):
        app = self.make_test_app()
        app.app.history['mymodule.AnotherType'] = [10, 20, 30, 40, 50]
        resp = app.get('/_dozer/?filter=type')
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<input name="filter" value="type"/>', resp)
        self.assertIn('mymodule.AnotherType', resp)
        self.assertIn('mymodule.MyType', resp)

        resp = app.get('/_dozer/?filter=another')
        self.assertEqual(resp.status_int, 200)
        self.assertIn('<input name="filter" value="another"/>', resp)
        self.assertIn('mymodule.AnotherType', resp)
        self.assertNotIn('mymodule.MyType', resp)

    def test_dozer_filter_broken_re_500_with_traceback(self):
        app = self.make_test_app()
        resp = app.get('/_dozer/?filter=(', status=500)
        self.assertEqual(resp.status_int, 500)
        self.assertIn('500 Internal Server Error', resp)
        self.assertIn('Traceback (most recent call last)', resp)
        try:
            self.assertIn(
                'error: missing ), unterminated subpattern at position 0', resp
            )
        except AssertionError:  # pragma: PY2
            self.assertIn('error: unbalanced parenthesis', resp)  # py2
