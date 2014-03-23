import unittest

from ..base import (
    DataDescription,
    DataDescriptionSubheader,
    DataDescriptionSubheaderOrder,
    DataDescriptionSubheaderSize,
    Field,
    OrderedField,
)


class TestField(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(ValueError):
            Field("a", "unknown_type")

        with self.assertRaises(ValueError):
            Field("title with space")

    def test_str_no_type(self):
        self.assertEqual(str(Field("a")), "a")
        self.assertEqual(str(Field("a", None)), "a")

    def test_str_with_type(self):
        self.assertEqual(str(Field("a", "str")), "a:str")

    def test__eq__(self):
        self.assertEqual(Field("a"), Field("a"))
        self.assertEqual(Field("a"), Field("a", None))
        self.assertEqual(Field("a", "str"), Field("a", "str"))

        self.assertNotEqual(Field("a"), Field("b"))
        self.assertNotEqual(Field("a"), Field("a", "str"))
        self.assertNotEqual(Field("a", "int"), Field("a", "str"))

    def test_parse(self):
        self.assertEqual(Field.parse("a"), Field("a"))
        self.assertEqual(Field.parse("a:str"), Field("a", "str"))

    def test_parse_error(self):
        with self.assertRaises(ValueError):
            Field.parse("a:")

        with self.assertRaises(ValueError):
            Field.parse("a str")


class TestOrderedField(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(ValueError):
            OrderedField("field with space")

        with self.assertRaises(ValueError):
            OrderedField("a", sort_type="unknown sort type")

        with self.assertRaises(ValueError):
            OrderedField("a", sort_order="unknown sort order")

    def test__eq__(self):
        self.assertEqual(OrderedField("a"), OrderedField("a"))
        self.assertEqual(OrderedField("a"), OrderedField("a", sort_type=""))
        self.assertEqual(OrderedField("a"), OrderedField("a", sort_order=""))
        self.assertEqual(
            OrderedField("a"), OrderedField("a", sort_type="", sort_order=""))
        self.assertEqual(
            OrderedField("a", sort_type="n"),
            OrderedField("a", sort_type="n")
        )
        self.assertEqual(
            OrderedField("a", sort_order="r"),
            OrderedField("a", sort_order="r")
        )
        self.assertEqual(
            OrderedField("a", sort_type="n", sort_order="r"),
            OrderedField("a", sort_type="n", sort_order="r")
        )

        self.assertNotEqual(OrderedField("a"), OrderedField("b"))
        self.assertNotEqual(
            OrderedField("a"), OrderedField("a", sort_order="r"))
        self.assertNotEqual(
            OrderedField("a"), OrderedField("a", sort_type="n"))

    def test_parse(self):
        self.assertEqual(OrderedField.parse("a:asc"), OrderedField("a"))
        self.assertEqual(
            OrderedField.parse("a:desc"), OrderedField("a", sort_order="r"))
        self.assertEqual(
            OrderedField.parse("a:asc:month"),
            OrderedField("a", sort_type="M"))
        self.assertEqual(
            OrderedField.parse("a:asc:random"),
            OrderedField("a", sort_type="R"))
        self.assertEqual(
            OrderedField.parse("a:asc:version"),
            OrderedField("a", sort_type="V"))
        self.assertEqual(
            OrderedField.parse("a:asc:general-numeric"),
            OrderedField("a", sort_type="g"))
        self.assertEqual(
            OrderedField.parse("a:asc:human-numeric"),
            OrderedField("a", sort_type="h"))
        self.assertEqual(
            OrderedField.parse("a:asc:numeric"),
            OrderedField("a", sort_type="n"))
        self.assertEqual(
            OrderedField.parse("a:desc:numeric"),
            OrderedField("a", sort_type="n", sort_order="r"))

    def test_parse_error(self):
        with self.assertRaises(ValueError):
            OrderedField.parse("a:")

        with self.assertRaises(ValueError):
            OrderedField.parse("a:r")

        with self.assertRaises(ValueError):
            OrderedField.parse("a:numeric")

        with self.assertRaises(ValueError):
            OrderedField.parse("a:asc:")

        with self.assertRaises(ValueError):
            OrderedField.parse("a:desc:")

        with self.assertRaises(ValueError):
            OrderedField.parse("a:asc:num")

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
    def setUp(self):
        self.subheader1 = DataDescriptionSubheader("key", "value")
        self.subheader2 = DataDescriptionSubheader("key", "value")
        self.subheader3 = DataDescriptionSubheader("ORDER", "a:asc b:desc")

    def test_str(self):
        self.assertEqual(str(self.subheader1), "KEY: value")
        self.assertEqual(str(self.subheader3), "ORDER: a:asc b:desc")

    def test__eq__(self):
        self.assertEqual(self.subheader1, self.subheader2)
        self.assertNotEqual(self.subheader1, self.subheader3)

    def test__eq__inherited(self):
        class DataDescriptionSubheaderChild(DataDescriptionSubheader):
            pass

        subheader_child1 = DataDescriptionSubheaderChild(
            self.subheader1.key, self.subheader1.value)
        subheader_child2 = DataDescriptionSubheaderChild(
            self.subheader2.key, self.subheader2.value)
        self.assertNotEqual(self.subheader1, subheader_child1)
        self.assertEqual(subheader_child1, subheader_child2)

    def test_parse(self):
        self.assertEqual(
            DataDescriptionSubheader.parse("key: value"),
            self.subheader1,
        )
        self.assertEqual(
            DataDescriptionSubheader.parse("ORDER: a:asc b:desc"),
            self.subheader3,
        )

    def test_parse_incorrect(self):
        DataDescriptionSubheader.parse("key: value")
        with self.assertRaises(ValueError):
            DataDescriptionSubheader.parse("key value")

        with self.assertRaises(ValueError):
            DataDescriptionSubheader.parse("key:value")


class TestDataDescriptionSubheaderOrder(unittest.TestCase):
    def setUp(self):
        self.subheader = DataDescriptionSubheaderOrder(
            "ORDER", "a:asc b:desc:numeric")
        self.ordered_fields = [
            OrderedField("a"),
            OrderedField("b", sort_type="n", sort_order="r"),
        ]

    def test_init(self):
        self.assertEqual(self.subheader.ordered_fields, self.ordered_fields)

    def test_parse(self):
        subheader = DataDescriptionSubheaderOrder.parse(str(self.subheader))
        self.assertEqual(self.subheader, subheader)


class TestDataDescriptionSubheaderSize(unittest.TestCase):
    def test_init_value(self):
        subheader1 = DataDescriptionSubheaderSize("size", 1)
        subheader2 = DataDescriptionSubheaderSize("size", "1")
        self.assertEqual(subheader1.value, 1)
        self.assertEqual(subheader2.value, 1)
        self.assertEqual(subheader1, subheader2)


class TestDataDescription(unittest.TestCase):
    def setUp(self):
        self.fields = (
            Field("a", "float"),
            Field("b", "bool"),
            Field("c"),
        )
        self.subheaders = (
            DataDescriptionSubheaderSize("SIZE", 1),
            DataDescriptionSubheaderOrder("ORDER", "c:asc a:desc:numeric"),
        )
        meta = "Data description and licence could be here. Even #META: tags!"
        self.meta = DataDescriptionSubheader("META", meta)
        self.data_description = DataDescription(
            fields=self.fields,
            subheaders=self.subheaders,
            meta=self.meta
        )
        self.header = "# a:float b:bool c #SIZE: 1" +\
            " #ORDER: c:asc a:desc:numeric #META: {}".format(meta)

    def test_str(self):
        self.assertEqual(str(self.data_description), self.header)

    def test_str_no_meta(self):
        data_description = DataDescription(
            fields=self.fields,
            subheaders=self.subheaders,
        )
        header = "# a:float b:bool c #SIZE: 1 #ORDER: c:asc a:desc:numeric"
        self.assertEqual(str(data_description), header)

    def test__eq__fields(self):
        data_description = DataDescription(
            fields=self.fields,
            subheaders=self.subheaders,
            meta=self.meta
        )
        self.assertEqual(self.data_description, data_description)

        data_description = DataDescription(
            fields=self.fields[1:],
            subheaders=self.subheaders,
            meta=self.meta
        )
        self.assertNotEqual(self.data_description, data_description)
        data_description = DataDescription(
            fields=self.fields[1:2] + self.fields[0:1] + self.fields[2:],
            subheaders=self.subheaders,
            meta=self.meta
        )
        self.assertNotEqual(self.data_description, data_description)

    def test__eq__subheaders(self):
        data_description = DataDescription(
            fields=self.fields,
            subheaders=self.subheaders[1:],
            meta=self.meta
        )
        self.assertNotEqual(self.data_description, data_description)
        data_description = DataDescription(
            fields=self.fields,
            subheaders=self.subheaders[1:] + self.subheaders[0:1],
            meta=self.meta
        )
        self.assertEqual(self.data_description, data_description)

    def test__eq__meta(self):
        meta = DataDescriptionSubheader("META", self.meta.value[:-1])
        data_description = DataDescription(
            fields=self.fields,
            subheaders=self.subheaders,
            meta=meta
        )
        self.assertNotEqual(self.data_description, data_description)

    def test_parse(self):
        self.assertEqual(
            DataDescription.parse(str(self.data_description)),
            self.data_description
        )

    def test_parse_error(self):
        DataDescription.parse("# ")
        with self.assertRaises(ValueError):
            DataDescription.parse("")

        with self.assertRaises(ValueError):
            DataDescription.parse("#")

        DataDescription.parse("# a")
        with self.assertRaises(ValueError):
            DataDescription.parse("a")

        with self.assertRaises(ValueError):
            DataDescription.parse("#a")

        DataDescription.parse("# a b #SIZE: 1")
        with self.assertRaises(ValueError):
            DataDescription.parse("# a b#SIZE: 1")

        DataDescription.parse("# a b #SIZE: 1 #ORDER: a:asc")
        with self.assertRaises(ValueError):
            DataDescription.parse("# a b #SIZE: 1 ##ORDER: a:asc")

        DataDescription.parse("# a b #ORDER: b:asc")
        with self.assertRaises(ValueError):
            DataDescription.parse("# a #ORDER: b:asc")
