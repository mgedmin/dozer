import unittest

from dozer.leak import Dozer


class DozerForTests(Dozer):
    def __init__(self, app=None, *args, **kw):
        super(DozerForTests, self).__init__(app, *args, **kw)
    def _start_thread(self):
        pass
    def _maybe_warn_about_PIL(self):
        pass


class EvilProxyClass(object):

    def __init__(self, obj):
        self.obj = obj

    @property
    def __module__(self):
        return self.obj.__module__

    @property
    def __name__(self):
        return self.obj.__name__


class TestDozer(unittest.TestCase):

    def test_tick_handles_types_with_broken_module(self):
        # https://bitbucket.org/bbangert/dozer/issue/3/cannot-user-operator-between-property-and
        dozer = DozerForTests()
        evil_proxy = EvilProxyClass(object) # keep a reference to it
        dozer.tick()

