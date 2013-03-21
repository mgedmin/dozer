import unittest

from dozer.util import asbool


class TestGlobals(unittest.TestCase):

    def check_true(self, value):
        self.assertTrue(asbool(value), repr(value))

    def check_false(self, value):
        self.assertFalse(asbool(value), repr(value))

    def test_asbool(self):
        true_values = ['true', 'yes', 'on', 'y', 't', '1']
        for v in true_values:
            self.check_true(v)
            self.check_true(v.upper())
            self.check_true(' %s ' % v.title())
        self.assertTrue(asbool(True))
        self.assertTrue(asbool(1))
        false_values = ['false', 'no', 'off', 'n', 'f', '0']
        for v in false_values:
            self.check_false(v)
            self.check_false(v.upper())
            self.check_false(' %s ' % v.title())
        self.assertFalse(asbool(False))
        self.assertFalse(asbool(0))
        self.assertRaises(ValueError, asbool, 'maybe')
