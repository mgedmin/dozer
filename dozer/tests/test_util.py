import base64
import unittest
from operator import itemgetter

from dozer.util import (
    asbool,
    check_basic_auth,
    monotonicity,
    parse_basic_auth,
    sort_dict_by_val,
    unauthorized,
)


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


class TestBasicAuth(unittest.TestCase):

    credentials = ('admin', 'secret')

    def make_header(self, userpass):
        token = base64.b64encode(userpass.encode()).decode()
        return 'Basic %s' % token

    def test_parse_basic_auth_pair(self):
        self.assertEqual(parse_basic_auth(('admin', 'secret')),
                         ('admin', 'secret'))
        self.assertEqual(parse_basic_auth(['admin', 'secret']),
                         ('admin', 'secret'))

    def test_parse_basic_auth_string(self):
        self.assertEqual(parse_basic_auth('admin:secret'),
                         ('admin', 'secret'))
        self.assertEqual(parse_basic_auth('admin:se:cret'),
                         ('admin', 'se:cret'))

    def test_parse_basic_auth_invalid(self):
        with self.assertRaises(ValueError):
            parse_basic_auth('admin')  # a string without a colon
        with self.assertRaises(ValueError):
            parse_basic_auth(('admin', 'secret', 'extra'))
        with self.assertRaises(ValueError):
            parse_basic_auth(42)

    def test_check_basic_auth(self):
        self.assertTrue(
            check_basic_auth(self.make_header('admin:secret'),
                             self.credentials))
        self.assertTrue(
            check_basic_auth(self.make_header('admin:se:cret'),
                             ('admin', 'se:cret')))

    def test_check_basic_auth_unpadded_base64(self):
        header = self.make_header('admin:secret').rstrip('=')
        self.assertTrue(check_basic_auth(header, self.credentials))

    def test_check_basic_auth_missing_header(self):
        self.assertFalse(check_basic_auth(None, self.credentials))
        self.assertFalse(check_basic_auth('', self.credentials))

    def test_check_basic_auth_malformed_header(self):
        self.assertFalse(check_basic_auth('Basic', self.credentials))
        self.assertFalse(check_basic_auth('Basic !!!', self.credentials))
        self.assertFalse(check_basic_auth(
            self.make_header('no-colon-here'), self.credentials))

    def test_check_basic_auth_wrong_scheme(self):
        self.assertFalse(check_basic_auth('Bearer sometoken',
                                          self.credentials))

    def test_check_basic_auth_wrong_credentials(self):
        self.assertFalse(check_basic_auth(
            self.make_header('admin:wrong'), self.credentials))
        self.assertFalse(check_basic_auth(
            self.make_header('nobody:secret'), self.credentials))

    def test_unauthorized(self):
        resp = unauthorized()
        self.assertEqual(resp.status_int, 401)
        self.assertEqual(resp.headers['WWW-Authenticate'],
                         'Basic realm="Dozer"')
