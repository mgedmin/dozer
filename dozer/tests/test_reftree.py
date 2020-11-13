import gc
import unittest

try:
    from cStringIO import StringIO
except ImportError:
    # Python 3.x
    from io import StringIO

from mock import patch

from dozer.reftree import Tree, ReferentTree, ReferrerTree, CircularReferents
from dozer.reftree import get_repr, count_objects, repr_dict, repr_set


class TestTree(unittest.TestCase):

    def test_walk_max_results(self):
        tree = Tree(None, None)
        tree._gen = lambda x: list(range(20))
        res = list(tree.walk(maxresults=3))
        self.assertEqual(res,
                         [0, 1, 2, (0, 0, "==== Max results reached ====")])

    def test_print_tree(self):
        tree = Tree(None, None)
        tree._gen = lambda x: [(0, 12345, 'ref1'), (1, 23456, 'ref2')]
        with patch('sys.stdout', StringIO()) as stdout:
            tree.print_tree()
            self.assertEqual(stdout.getvalue(),
                             "    12345  ref1\n"
                             "    23456    ref2\n")


class MyObj(object):

    def __init__(self, **kw):
        self.__dict__.update(kw)

    def __repr__(self):
        return getattr(self, 'name', 'unnamed-MyObj')


class Unrepresentable(object):
    def __repr__(self):
        raise Exception('haha you cannot represent me')


class TestGlobals(unittest.TestCase):

    def test_repr_dict_unsortable(self):
        repr_dict({int: 'int', str: 'str'})

    def test_repr_set_unsortable(self):
        repr_set({int, str})

    def test_get_repr_unrepresentable(self):
        # repr(Exception('foo')) is "Exception('foo',)" on Python < 3.7
        # repr(Exception('foo')) is "Exception('foo')" on Python >= 3.7
        self.assertEqual(
            get_repr(Unrepresentable()).replace(',)', ')'),
            "unrepresentable object: Exception('haha you cannot represent me')")

    def test_count_objects(self):
        gc.collect()
        obj = MyObj()
        res = count_objects()
        self.assertIn((1, MyObj), [(n, c) for (n, c) in res if c is MyObj])


class TestReferentTree(unittest.TestCase):

    def make_tree(self):
        tree = ReferentTree(None, None)
        tree.maxdepth = 10
        tree.seen = {}
        return tree

    def test_gen(self):
        tree = self.make_tree()
        ref = MyObj(name='b')
        other = MyObj(name='c')
        obj = MyObj(name='a', ref=ref, other=other, again=other)
        tree.ignore(ref)
        res = list(tree._gen(obj))
        self.assertIn((1, id(other), 'c'), res)
        self.assertIn((1, id(other), '!c'), res)


class TestReferrerTree(unittest.TestCase):

    def make_tree(self, maxdepth=10):
        tree = ReferrerTree(None, None)
        tree.maxdepth = maxdepth
        tree.seen = {}
        return tree

    def test_gen(self):
        tree = self.make_tree()
        obj = MyObj()
        ref = MyObj(name='a', obj=obj)
        res = list(tree._gen(obj))
        self.assertIn((1, id(ref), 'a'), res)

    def test_gen_maxdepth(self):
        tree = self.make_tree(maxdepth=1)
        obj = MyObj()
        # On Python 3.7 the local code frame is somehow not counted
        # as a referer!  So we need to create at least one more reference.
        ref = MyObj(name='a', obj=obj)  # noqa
        res = list(tree._gen(obj))
        self.assertIn((1, 0, "---- Max depth reached ----"), res)


class TestCircularReferents(unittest.TestCase):

    def make_tree(self, obj=None):
        tree = CircularReferents(obj, None)
        return tree

    def make_cycle(self):
        obj = MyObj(name='obj',
                    a=MyObj(name='a', c=MyObj(name='c')),
                    b=MyObj(name='b'))
        obj.b.obj = obj # make a cycle
        return obj

    def test_walk(self):
        obj = self.make_cycle()
        tree = self.make_tree(obj)
        res = list(tree.walk())
        self.assertEqual(len(res), 1) # one cycle
        self.assertEqual(len(res[0]), 4) # MyObj -> __dict__ -> MyObj -> __dict__

    def test_walk_maxresults(self):
        obj = self.make_cycle()
        tree = self.make_tree(obj)
        res = list(tree.walk(maxresults=1))
        self.assertIn((0, 0, "==== Max results reached ===="), res)

    def test_walk_maxdepth(self):
        obj = self.make_cycle()
        tree = self.make_tree(obj)
        res = list(tree.walk(maxdepth=2))
        self.assertGreater(tree.stops, 0)

    def test_print_tree(self):
        obj = self.make_cycle()
        tree = self.make_tree(obj)
        with patch('sys.stdout', StringIO()) as stdout:
            tree.print_tree(maxdepth=5)
            self.assertEqual(
                stdout.getvalue(),
                '''["dict of len 3: {'a': a, 'b': b, 'name': 'obj'}", 'b','''
                ''' "dict of len 2: {'name': 'b', 'obj': obj}", 'obj']\n'''
                '''2 paths stopped because max depth reached\n''')
