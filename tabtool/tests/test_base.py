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

    def test_sort_flag(self):
        self.assertEqual(OrderedField("a").sort_flag, "")
        self.assertEqual(OrderedField("a", sort_type="M").sort_flag, "M")
        self.assertEqual(OrderedField("a", sort_type="R").sort_flag, "R")
        self.assertEqual(OrderedField("a", sort_type="V").sort_flag, "V")
        self.assertEqual(OrderedField("a", sort_type="g").sort_flag, "g")
        self.assertEqual(OrderedField("a", sort_type="h").sort_flag, "h")
        self.assertEqual(OrderedField("a", sort_type="n").sort_flag, "n")

        self.assertEqual(OrderedField("a", is_reverse=True).sort_flag, "r")
        self.assertEqual(
            OrderedField("a", sort_type="M", is_reverse=True).sort_flag, "Mr")
        self.assertEqual(
            OrderedField("a", sort_type="R", is_reverse=True).sort_flag, "Rr")
        self.assertEqual(
            OrderedField("a", sort_type="V", is_reverse=True).sort_flag, "Vr")
        self.assertEqual(
            OrderedField("a", sort_type="g", is_reverse=True).sort_flag, "gr")
        self.assertEqual(
            OrderedField("a", sort_type="h", is_reverse=True).sort_flag, "hr")
        self.assertEqual(
            OrderedField("a", sort_type="n", is_reverse=True).sort_flag, "nr")
