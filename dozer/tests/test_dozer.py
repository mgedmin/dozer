import shutil
import tempfile
import unittest

from dozer import (
    Dozer, Logview, Profiler,
    profile_filter_factory, dozer_filter_factory, logview_filter_factory,
    profile_filter_app_factory, dozer_filter_app_factory,
    logview_filter_app_factory)


class TestFactories(unittest.TestCase):

    def setUp(self):
        self.tmpdir = None

    def tearDown(self):
        if self.tmpdir:
            shutil.rmtree(self.tmpdir)

    def make_tmp_dir(self):
        if not self.tmpdir:
            self.tmpdir = tempfile.mkdtemp('dozer-tests-')
        return self.tmpdir

    def test_profile_filter_factory(self):
        self._test_filter_factory(profile_filter_factory, Profiler,
                                  profile_path=self.make_tmp_dir())

    def test_dozer_filter_factory(self):
        self._test_filter_factory(dozer_filter_factory, Dozer)

    def test_logview_filter_factory(self):
        self._test_filter_factory(logview_filter_factory, Logview)

    def _test_filter_factory(self, factory, expect, global_conf={}, **kwargs):
        app = object()
        filter = factory(global_conf, **kwargs)
        wrapped_app = filter(app)
        self.assertTrue(isinstance(wrapped_app, expect))

    def test_profile_filter_app_factory(self):
        self._test_filter_app_factory(profile_filter_app_factory, Profiler,
                                      profile_path=self.make_tmp_dir())

    def test_dozer_filter_app_factory(self):
        self._test_filter_app_factory(dozer_filter_app_factory, Dozer)

    def test_logview_filter_app_factory(self):
        self._test_filter_app_factory(logview_filter_app_factory, Logview)

    def _test_filter_app_factory(self, factory, expect, global_conf={},
                                 **kwargs):
        app = object()
        wrapped_app = factory(app, global_conf, **kwargs)
        self.assertTrue(isinstance(wrapped_app, expect))

