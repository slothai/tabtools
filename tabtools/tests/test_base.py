import pytest

from ..base import Field, Header, Subheader, SubheaderCount


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


class TestSubheader:
    def test_str(self):
        assert str(Subheader("key", "value")) == "KEY:value"
        assert str(Subheader("order", "a:asc b:desc")) == "ORDER:a:asc b:desc"

    def test__eq__(self):
        assert Subheader("key", "value") == Subheader("KEY", "value")
        assert Subheader("key", "value") != Subheader("order", "a:asc b:desc")

    def test__eq__inherited(self):
        class SubheaderChild(Subheader):
            pass

        subheader_child1 = SubheaderChild("key", "value")
        subheader_child2 = SubheaderChild("key", "value")

        assert subheader_child1 == subheader_child2
        assert Subheader("key", "value") != subheader_child1

    def test_parse(self):
        assert Subheader.parse("key:value") == Subheader("key", "value")
        assert Subheader.parse("ORDER:a:asc b:desc") == Subheader("order", "a:asc b:desc")

    def test_parse_incorrect(self):
        Subheader.parse("key:value")
        with pytest.raises(ValueError):
            Subheader.parse("key value")

    def test_union(self):
        assert Subheader.union(
            Subheader("k", "v1"),
            Subheader("k", "v2")
        ) == Subheader("k", "?")

    def test_union_error(self):
        with pytest.raises(ValueError):
            Subheader.union()

        with pytest.raises(ValueError):
            Subheader.union(
                Subheader("k1", "v"),
                Subheader("k2", "v")
            )


class TestSubheaderCount:
    def test_init_value(self):
        subheader1 = SubheaderCount("count", 1)
        subheader2 = SubheaderCount("count", "1")
        assert subheader1.value == 1
        assert subheader2.value == 1
        assert subheader1 == subheader2

    def test_merge(self):
        assert SubheaderCount.union(
            SubheaderCount("count", 1),
            SubheaderCount("count", 2)
        ) == SubheaderCount("count", 3)


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
