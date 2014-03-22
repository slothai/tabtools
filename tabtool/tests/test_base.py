import unittest

from ..base import (
    Field, OrderedField, DataDescriptionSubheader
)


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

        self.assertEqual(OrderedField("a", sort_order="r").sort_flag, "r")
        self.assertEqual(
            OrderedField("a", sort_type="M", sort_order="r").sort_flag, "Mr")
        self.assertEqual(
            OrderedField("a", sort_type="R", sort_order="r").sort_flag, "Rr")
        self.assertEqual(
            OrderedField("a", sort_type="V", sort_order="r").sort_flag, "Vr")
        self.assertEqual(
            OrderedField("a", sort_type="g", sort_order="r").sort_flag, "gr")
        self.assertEqual(
            OrderedField("a", sort_type="h", sort_order="r").sort_flag, "hr")
        self.assertEqual(
            OrderedField("a", sort_type="n", sort_order="r").sort_flag, "nr")

    def test_str_no_type_no_ordering(self):
        self.assertEqual(str(OrderedField("a")), "a:asc")

    def test_str_no_type(self):
        self.assertEqual(str(OrderedField("a", sort_order="")), "a:asc")
        self.assertEqual(str(OrderedField("a", sort_order="r")), "a:desc")

    def test_str_no_ordering(self):
        self.assertEqual(str(OrderedField("a", sort_type="")), "a:asc")
        self.assertEqual(str(OrderedField("a", sort_type="M")), "a:asc:month")
        self.assertEqual(str(OrderedField("a", sort_type="R")), "a:asc:random")
        self.assertEqual(
            str(OrderedField("a", sort_type="V")), "a:asc:version")
        self.assertEqual(
            str(OrderedField("a", sort_type="g")), "a:asc:general-numeric")
        self.assertEqual(
            str(OrderedField("a", sort_type="h")), "a:asc:human-numeric")
        self.assertEqual(
            str(OrderedField("a", sort_type="n")), "a:asc:numeric")

    def test_str(self):
        self.assertEqual(
            str(OrderedField("a", sort_type="", sort_order="r")), "a:desc")
        self.assertEqual(
            str(OrderedField("a", sort_type="M", sort_order="r")),
            "a:desc:month")
        self.assertEqual(
            str(OrderedField("a", sort_type="R", sort_order="r")),
            "a:desc:random")
        self.assertEqual(
            str(OrderedField("a", sort_type="V", sort_order="r")),
            "a:desc:version")
        self.assertEqual(
            str(OrderedField("a", sort_type="g", sort_order="r")),
            "a:desc:general-numeric")
        self.assertEqual(
            str(OrderedField("a", sort_type="h", sort_order="r")),
            "a:desc:human-numeric")
        self.assertEqual(
            str(OrderedField("a", sort_type="n", sort_order="r")),
            "a:desc:numeric")


class TestDataDescriptionSubheader(unittest.TestCase):
    def test_str(self):
        subheader = DataDescriptionSubheader("key", "value")
        self.assertEqual(str(subheader), " #key: value")
        subheader = DataDescriptionSubheader("ORDER", "a:asc b:desc")
        self.assertEqual(str(subheader), " #ORDER: a:asc b:desc")

    def test_parse(self):
        subheader = DataDescriptionSubheader("key", "value")
        self.assertEqual(
            subheader, DataDescriptionSubheader.parse(" #key: value"))
        subheader = DataDescriptionSubheader("ORDER", "a:asc b:desc")
        self.assertEqual(
            subheader, DataDescriptionSubheader.parse(" #ORDER: a:asc b:desc"))
