import pytest

from ..base import (Field, Header, OrderedField, Subheader, SubheaderCount,
                    SubheaderOrder)


class TestField:
    def test_init(self):
        with pytest.raises(ValueError):
            Field("")

        with pytest.raises(ValueError):
            Field("a", "unknown_type")

        with pytest.raises(ValueError):
            Field("title with space")

    def test_str_no_type(self):
        assert str(Field("a")) == "a"
        assert str(Field("a", None)) ==  "a"

    def test_str_with_type(self):
        assert str(Field("a", Field.TYPES.STRING)) == "a:str"

    def test__eq__(self):
        assert Field("a") == Field("a")
        assert Field("a") == Field("a", None)
        assert Field("a", Field.TYPES.STRING) == Field("a", Field.TYPES.STRING)

        assert Field("a") != Field("b")
        assert Field("a") != Field("a", Field.TYPES.STRING)
        assert Field("a", Field.TYPES.NUMBER) != Field("a", Field.TYPES.STRING)

    def test_parse(self):
        assert Field.parse("a") == Field("a")
        assert Field.parse("a:str") == Field("a", Field.TYPES.STRING)

    def test_parse_error(self):
        with pytest.raises(ValueError):
            Field.parse("a:")  # type is missing

        with pytest.raises(ValueError):
            Field.parse("a str")  # space in field title

    def test_union_simple(self):
        assert Field.union(Field("a")) ==  Field("a")
        assert Field.union(Field("a"), Field("a")) == Field("a")

    def test_union_different_names(self):
        assert Field.union(Field("a"), Field("b")) == Field("a")
        assert Field.union(Field("b"), Field("a")) == Field("b")

    def test_union_same_type(self):
        assert Field.union(Field("a"), Field("a")) == Field("a")

        for t in Field.TYPES:
            assert Field.union(Field("a", t), Field("a", t)) == Field("a", t)

    def test_union_different_types(self):
        assert Field.union(Field("a", Field.TYPES.STRING), Field("a")) == Field("a")
        assert Field.union(Field("a", Field.TYPES.NUMBER), Field("a")) == Field("a")
        assert Field.union(Field("a", Field.TYPES.STRING), Field("a", Field.TYPES.NUMBER)) == Field("a", Field.TYPES.STRING)

    def test_union_error(self):
        with pytest.raises(ValueError):
            Field.union()


class TestOrderedField:
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


class TestSubheader:
    def setUp(self):
        self.subheader1 = Subheader("key", "value")
        self.subheader2 = Subheader("key", "value")
        self.subheader3 = Subheader("ORDER", "a:asc b:desc")

    def test_str(self):
        self.assertEqual(str(self.subheader1), "KEY: value")
        self.assertEqual(str(self.subheader3), "ORDER: a:asc b:desc")

    def test__eq__(self):
        self.assertEqual(self.subheader1, self.subheader2)
        self.assertNotEqual(self.subheader1, self.subheader3)

    def test__eq__inherited(self):
        class SubheaderChild(Subheader):
            pass

        subheader_child1 = SubheaderChild(
            self.subheader1.key, self.subheader1.value)
        subheader_child2 = SubheaderChild(
            self.subheader2.key, self.subheader2.value)
        self.assertNotEqual(self.subheader1, subheader_child1)
        self.assertEqual(subheader_child1, subheader_child2)

    def test_parse(self):
        self.assertEqual(
            Subheader.parse("key: value"),
            self.subheader1,
        )
        self.assertEqual(
            Subheader.parse("ORDER: a:asc b:desc"),
            self.subheader3,
        )

    def test_parse_incorrect(self):
        Subheader.parse("key: value")
        with self.assertRaises(ValueError):
            Subheader.parse("key value")

        with self.assertRaises(ValueError):
            Subheader.parse("key:value")

    def test_merge(self):
        self.assertEqual(
            Subheader.merge(
                Subheader("k", "v1"),
                Subheader("k", "v2")
            ),
            Subheader("k", "")
        )

    def test_merge_error(self):
        with self.assertRaises(ValueError):
            Subheader.merge()
            Subheader.merge(
                Subheader("k1", "v"),
                Subheader("k2", "v")
            )


class TestSubheaderOrder:
    def setUp(self):
        self.subheader = SubheaderOrder(
            "ORDER", "a:asc\tb:desc:numeric")
        self.ordered_fields = [
            OrderedField("a"),
            OrderedField("b", sort_type="n", sort_order="r"),
        ]

    def test_init(self):
        self.assertEqual(self.subheader.ordered_fields, self.ordered_fields)

    def test_parse(self):
        subheader = SubheaderOrder.parse(str(self.subheader))
        self.assertEqual(self.subheader, subheader)


class TestSubheaderCount:
    def test_init_value(self):
        subheader1 = SubheaderCount("count", 1)
        subheader2 = SubheaderCount("count", "1")
        self.assertEqual(subheader1.value, 1)
        self.assertEqual(subheader2.value, 1)
        self.assertEqual(subheader1, subheader2)

    def test_merge(self):
        self.assertEqual(
            SubheaderCount.merge(
                SubheaderCount("count", 1),
                SubheaderCount("count", 1)
            ),
            SubheaderCount("count", 2)
        )


class TestHeader:
    def setUp(self):
        self.fields = (
            Field("a", "float"),
            Field("b", "bool"),
            Field("c"),
        )
        self.subheaders = (
            SubheaderCount("COUNT", 1),
            SubheaderOrder("ORDER", "c:asc\ta:desc:numeric"),
        )
        meta = "Data description and licence could be here. Even #META: tags!"
        self.meta = Subheader("META", meta)
        self.data_description = Header(
            fields=self.fields,
            subheaders=self.subheaders,
            meta=self.meta
        )
        self.header = "# a:float\tb:bool\tc #COUNT: 1" +\
            " #ORDER: c:asc\ta:desc:numeric #META: {}".format(meta)

    def test_str(self):
        self.assertEqual(str(self.data_description), self.header)

    def test_str_no_meta(self):
        data_description = Header(
            fields=self.fields,
            subheaders=self.subheaders,
        )
        header = "# a:float\tb:bool\tc #COUNT: 1 #ORDER: c:asc\ta:desc:numeric"
        self.assertEqual(str(data_description), header)

    def test__eq__fields(self):
        data_description = Header(
            fields=self.fields,
            subheaders=self.subheaders,
            meta=self.meta
        )
        self.assertEqual(self.data_description, data_description)

        data_description = Header(
            fields=self.fields[1:],
            subheaders=self.subheaders,
            meta=self.meta
        )
        self.assertNotEqual(self.data_description, data_description)
        data_description = Header(
            fields=self.fields[1:2] + self.fields[0:1] + self.fields[2:],
            subheaders=self.subheaders,
            meta=self.meta
        )
        self.assertNotEqual(self.data_description, data_description)

    def test__eq__subheaders(self):
        data_description = Header(
            fields=self.fields,
            subheaders=self.subheaders[1:],
            meta=self.meta
        )
        self.assertNotEqual(self.data_description, data_description)
        data_description = Header(
            fields=self.fields,
            subheaders=self.subheaders[1:] + self.subheaders[0:1],
            meta=self.meta
        )
        self.assertEqual(self.data_description, data_description)

    def test__eq__meta(self):
        meta = Subheader("META", self.meta.value[:-1])
        data_description = Header(
            fields=self.fields,
            subheaders=self.subheaders,
            meta=meta
        )
        self.assertNotEqual(self.data_description, data_description)

    def test_parse(self):
        self.assertEqual(
            Header.parse(str(self.data_description)),
            self.data_description
        )

    def test_parse_error(self):
        Header.parse("# ")
        with self.assertRaises(ValueError):
            Header.parse("")

        with self.assertRaises(ValueError):
            Header.parse("#")

        Header.parse("# a")
        with self.assertRaises(ValueError):
            Header.parse("a")

        with self.assertRaises(ValueError):
            Header.parse("#a")

        Header.parse("# a\tb #COUNT: 1")
        with self.assertRaises(ValueError):
            Header.parse("# a\tb#COUNT: 1")

        Header.parse("# a\tb #COUNT: 1 #ORDER: a:asc")
        with self.assertRaises(ValueError):
            Header.parse("# a\tb #COUNT: 1 ##ORDER: a:asc")

        Header.parse("# a\tb #ORDER: b:asc")
        with self.assertRaises(ValueError):
            Header.parse("# a #ORDER: b:asc")

    def test_merge(self):
        dd1 = Header(
            fields=(
                Field("a", "int"),
                Field("b", "float"),
            ),
            subheaders=(
                HeaderSubheaderCount("COUNT", 1),
                HeaderSubheaderOrder("ORDER", "a:asc\tb:desc:numeric"),
            ),
            meta="meta1"
        )

        dd2 = Header(
            fields=(
                Field("a", "str"),
                Field("b", "bool"),
            ),
            subheaders=(
                SubheaderCount("COUNT", 1),
                SubheaderOrder("ORDER", "a:desc"),
            ),
            meta="meta1"
        )

        dd_expected = Header(
            fields=(
                Field("a", "str"),
                Field("b", "float"),
            ),
            subheaders=(
                SubheaderCount("COUNT", 2),
            ),
        )
        self.assertEqual(Header.merge(dd1, dd2), dd_expected)
