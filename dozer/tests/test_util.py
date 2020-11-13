import unittest
from operator import itemgetter

from dozer.util import asbool, monotonicity, sort_dict_by_val


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

    def test_cumulative_derivative(self):
        array_1 = [1, 2, 1, 2, 3]
        array_2 = [0, 0, 0, 0, 0]
        array_empty = []
        self.assertAlmostEqual(0.6, monotonicity(array_1))
        self.assertEqual(0, monotonicity(array_2))
        self.assertEqual(0, monotonicity(array_empty))

    def test_sort_dict_by_val(self):
        d = {
            'a': (5, 9),
            'b': (4, 2),
            'c': (6, 8)
        }
        key1 = itemgetter(0)
        key2 = itemgetter(1)

        s1 = sort_dict_by_val(d, key1)
        s2 = sort_dict_by_val(d, key2)

        self.assertEqual(s1[0][0], 'b')
        self.assertEqual(s1[1][0], 'a')
        self.assertEqual(s2[0][0], 'b')
        self.assertEqual(s2[1][0], 'c')
