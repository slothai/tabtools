import unittest

from ..base import Field, OrderedField


class TestField(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(ValueError):
            Field("a", "unknown_type")

    def test_str_no_type(self):
        self.assertEqual(str(Field("a")), "a")
        self.assertEqual(str(Field("a", None)), "a")

    def test_str_with_type(self):
        self.assertEqual(str(Field("a", "str")), "a:str")


class TestOrderedField(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(ValueError):
            OrderedField("a", sort_type="unknown sort type")
