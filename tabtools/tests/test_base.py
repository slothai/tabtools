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
    def setup_method(self, method):
        self.fields = (
            Field("a", Field.TYPES.NUMBER),
            Field("b", Field.TYPES.STRING),
            Field("c"),
        )
        self.subheaders = (
            SubheaderCount("COUNT", 1),
            Subheader("ORDER", "a:asc"),
        )

    def test_str(self):
        header = Header(
            delimiter='\t',
            fields=self.fields,
            subheaders=self.subheaders,
        )

        assert str(header) == "a:num\tb:str\tc #COUNT:1 #ORDER:a:asc"

        header.delimiter = ','
        assert str(header) == "a:num,b:str,c #COUNT:1 #ORDER:a:asc"

    def test__eq__fields(self):
        header1 = Header(
            delimiter='\t',
            fields=self.fields,
            subheaders=self.subheaders,
        )
        header2 = Header(
            delimiter='\t',
            fields=self.fields,
            subheaders=self.subheaders,
        )
        assert header1 == header2

        header2.fields=self.fields[1:]
        assert header1 != header2

        header2.fields=self.fields[1:2] + self.fields[0:1] + self.fields[2:]
        assert header1 != header2

    def test__eq__subheaders(self):
        header1 = Header(
            delimiter='\t',
            fields=self.fields,
            subheaders=self.subheaders,
        )
        header2 = Header(
            delimiter='\t',
            fields=self.fields,
            subheaders=self.subheaders[1:],
        )

        assert header1 != header2

        header2.subheaders=self.subheaders[1:] + self.subheaders[0:1]
        assert header1 == header2

    def test_generate(self):
        assert "f0,f1,f2" == str(Header.generate(',', 3))

    def test_parse(self):
        assert Header.parse("a:num\tb:str\tc #COUNT:1 #ORDER:a:asc") == Header(
            delimiter='\t',
            fields=self.fields,
            subheaders=self.subheaders
        )
        
        assert Header.parse("a:num,b:str,c #COUNT:1 #ORDER:a:asc") == Header(
            delimiter=',',
            fields=self.fields,
            subheaders=self.subheaders
        )

        assert Header.parse("a:num|b:str|c #COUNT:1 #ORDER:a:asc", delimiter="|") == Header(
            delimiter='|',
            fields=self.fields,
            subheaders=self.subheaders
        )

    def test_union(self):
        h1 = Header(
            delimiter="\t",
            fields=(
                Field("a", Field.TYPES.NUMBER),
                Field("b"),
            ),
            subheaders=(
                SubheaderCount("COUNT", 1),
                Subheader("ORDER", "a:asc\tb:desc"),
            )
        )

        h2 = Header(
            delimiter=",",
            fields=(
                Field("a", Field.TYPES.STRING),
                Field("b", Field.TYPES.NUMBER),
            ),
            subheaders=(
                SubheaderCount("COUNT", 1),
                Subheader("ORDER", "a:desc"),
            )
        )

        expected = Header(
            fields=(
                Field("a", Field.TYPES.STRING),
                Field("b"),
            ),
            subheaders=(
                SubheaderCount("COUNT", 2),
            ),
        )
        assert Header.union(h1, h2) == expected
