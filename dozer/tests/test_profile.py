import os
import sys
import shutil
import tempfile
import textwrap
import unittest
import pickle
from collections import namedtuple

try:
    from cStringIO import StringIO
except ImportError:
    # Python 3.x
    from io import StringIO

try:
    import __builtin__ as builtins
except ImportError:
    # Python 3.x
    import builtins

try:
    from unittest import skipIf
except ImportError:
    # Python 2.6
    def skipIf(condition, reason):
        def wrapper(fn):
            if condition:
                def empty_test(case):
                    pass
                empty_test.__doc__ = '%s skipped because %s' % (
                    fn.__name__, reason)
                return empty_test
            return fn
        return wrapper


from mock import patch
from webtest import TestApp

from dozer.profile import Profiler, label, graphlabel, setup_time, color
from dozer.profile import write_dot_graph


class TestGlobals(unittest.TestCase):

    def make_code_object(self):
        d = {}
        exec(compile(textwrap.dedent('''\
                         # skip a line to get a more interesting line number
                         def somefunc():
                             pass
                     '''), 'sourcefile.py', 'single'), d)
        return d['somefunc'].__code__

    def test_label(self):
        self.assertEqual(label('somefunc'), 'somefunc')

    def test_label_with_code_object(self):
        code = self.make_code_object()
        self.assertEqual(label(code), 'somefunc sourcefile.py:2')

    def test_graphlabel(self):
        # I don't know if this is a plausible example of things that can be
        # passed in, I just know the existing code gets rid of double quotes
        self.assertEqual(graphlabel('somefunc "dir with spaces/file.py":42'),
                         "somefunc 'dir with spaces/file.py':42")

    def test_setup_time(self):
        self.assertEqual(setup_time(0.004), '4.00')
        self.assertEqual(setup_time(0.00025), '0.25')

    def test_color(self):
        self.assertEqual(color(0), '#00002C')       # cold: darkish blue
        self.assertEqual(color(0.25), '#004C4C')    # cool: cyanish
        self.assertEqual(color(0.5), '#007900')     # medium: green
        self.assertEqual(color(0.75), '#B4B400')    # warm: very dark yellow
        self.assertEqual(color(1), '#FF0000')       # hot: red

    def test_write_dot_graph_very_very_fast_function(self):
        code = self.make_code_object()
        profile_entry = namedtuple('profile_entry', 'code totaltime calls')
        with patch.object(builtins, 'open', lambda *a: StringIO()) as output:
            data = [profile_entry(code=code, totaltime=1, calls=[])]
            tree = {'somefunc sourcefile.py:2': dict(cost=0)}
            write_dot_graph(data, tree, 'filename.gv')


class AppIter(list):
    def close(self):
        pass


def hello_world(environ, start_response):
    body = b'hello, world!'
    headers = [('Content-Type', 'text/html; charset=utf8'),
               ('Content-Length', str(len(body)))]
    start_response('200 Ok', headers)
    return AppIter([body])


class TestEntireStack(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp('dozer-tests-')

    def tearDown(self):
        os.chmod(self.tmpdir, 0o700)
        shutil.rmtree(self.tmpdir)

    def make_wsgi_app(self):
        profiler = Profiler(hello_world, profile_path=self.tmpdir)
        return profiler

    def make_test_app(self):
        return TestApp(self.make_wsgi_app())

    def list_profiles(self, suffix='.pkl'):
        return [fn[:-len(suffix)] for fn in os.listdir(self.tmpdir)
                if fn.endswith(suffix)]

    def record_profile(self, app):
        before = set(self.list_profiles())
        app.get('/')
        after = set(self.list_profiles())
        new = after - before
        self.assertEqual(len(new), 1)
        return next(iter(new))

    def save_fake_profile(self, prof_id, data):
        with open(os.path.join(self.tmpdir, '%s.pkl' % prof_id), 'wb') as f:
            f.write(data)

    def test_application_pass_through(self):
        app = self.make_test_app()
        resp = app.get('/')
        self.assertTrue('hello, world!' in resp)
        # a profile is created
        self.assertNotEqual(os.listdir(self.tmpdir), [])

    @skipIf(sys.platform == 'win32', 'Windows has a different permissions model')
    def test_cannot_save_profile(self):
        app = self.make_test_app()
        os.chmod(self.tmpdir, 0o500)
        self.assertRaises(OSError, self.record_profile, app)

    def test_appiter_close_is_called(self):
        app = self.make_test_app()
        with patch.object(AppIter, 'close') as close:
            app.get('/')
            self.assertEqual(close.call_count, 1)

    def test_application_ignore_some_paths(self):
        app = self.make_test_app()
        resp = app.get('/favicon.ico')
        self.assertTrue('hello, world!' in resp)
        self.assertEqual(os.listdir(self.tmpdir), [])

    def test_profiler_index(self):
        app = self.make_test_app()
        self.record_profile(app) # so the list is not empty
        resp = app.get('/_profiler')
        self.assertEqual(resp.status_int, 200)
        self.assertTrue('<table id="profile-list">' in resp)

    def test_profiler_index_empty(self):
        app = self.make_test_app()
        resp = app.get('/_profiler')
        self.assertEqual(resp.status_int, 200)
        self.assertTrue('<table id="profile-list">' in resp)

    def test_profiler_broken_pickle(self):
        app = self.make_test_app()
        self.save_fake_profile(42, b'not a pickle at all')
        resp = app.get('/_profiler')
        self.assertEqual(resp.status_int, 200)
        self.assertTrue('<table id="profile-list">' in resp)

    def test_profiler_empty_profile(self):
        app = self.make_test_app()
        self.save_fake_profile(42, pickle.dumps(dict(
            environ={'SCRIPT_NAME': '', 'PATH_INFO': '/', 'QUERY_STRING': ''},
            profile={},
        )))
        resp = app.get('/_profiler')
        self.assertEqual(resp.status_int, 200)
        self.assertTrue('<table id="profile-list">' in resp)

    def test_profiler_not_found(self):
        app = self.make_test_app()
        app.get('/_profiler/nosuchpage', status=404)

    def test_profiler_forbidden(self):
        app = self.make_test_app()
        app.get('/_profiler/profiler', status=403)

    def test_profiler_media(self):
        app = self.make_test_app()
        resp = app.get('/_profiler/media/css/profile.css')
        self.assertEqual(resp.status_int, 200)
        self.assertEqual(resp.content_type, 'text/css')
        self.assertTrue('#profile {' in resp)

    def test_profiler_show_no_id(self):
        app = self.make_test_app()
        app.get('/_profiler/show', status=404)

    def test_profiler_show(self):
        app = self.make_test_app()
        prof_id = self.record_profile(app)
        resp = app.get('/_profiler/show/%s' % prof_id)
        self.assertTrue('<div id="profiler">' in resp)

    def test_profiler_delete(self):
        app = self.make_test_app()
        prof_id = self.record_profile(app)
        resp = app.get('/_profiler/delete/%s' % prof_id)
        self.assertEqual(os.listdir(self.tmpdir), [])
        self.assertTrue('deleted' in resp)

    def test_profiler_delete_nonexistent(self):
        app = self.make_test_app()
        resp = app.get('/_profiler/delete/42')
        self.assertTrue('deleted' in resp)

    @skipIf(sys.platform == 'win32', 'Windows has a different permissions model')
    def test_profiler_delete_fails(self):
        app = self.make_test_app()
        prof_id = self.record_profile(app)
        os.chmod(self.tmpdir, 0o500)
        self.assertRaises(OSError, app.get, '/_profiler/delete/%s' % prof_id)

    def test_profiler_delete_all(self):
        app = self.make_test_app()
        self.record_profile(app)
        self.record_profile(app) # do it twice
        resp = app.get('/_profiler/delete', status=302)
        self.assertEqual(os.listdir(self.tmpdir), [])
        self.assertEqual(resp.location, 'http://localhost/_profiler/showall')

