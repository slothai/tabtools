import unittest

from ..base import Field, Header, Subheader, SubheaderCount


class TestField(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(ValueError):
            Field("")

        with self.assertRaises(ValueError):
            Field("a", "unknown_type")

        with self.assertRaises(ValueError):
            Field("title with space")

    def test_str_no_type(self):
        self.assertEqual(str(Field("a")), "a")
        self.assertEqual(str(Field("a", None)),  "a")

    def test_str_with_type(self):
        self.assertEqual(str(Field("a", Field.TYPES.STRING)), "a:str")

    def test__eq__(self):
        self.assertEqual(Field("a"), Field("a"))
        self.assertEqual(Field("a"), Field("a", None))
        self.assertEqual(Field("a", Field.TYPES.STRING), Field("a", Field.TYPES.STRING))

        self.assertNotEqual(Field("a"), Field("b"))
        self.assertNotEqual(Field("a"), Field("a", Field.TYPES.STRING))
        self.assertNotEqual(Field("a", Field.TYPES.NUMBER), Field("a", Field.TYPES.STRING))

    def test_parse(self):
        self.assertEqual(Field.parse("a"), Field("a"))
        self.assertEqual(Field.parse("a:str"), Field("a", Field.TYPES.STRING))

    def test_parse_error(self):
        with self.assertRaises(ValueError):
            Field.parse("a:")  # type is missing

        with self.assertRaises(ValueError):
            Field.parse("a str")  # space in field title

    def test_union_simple(self):
        self.assertEqual(Field.union(Field("a")),  Field("a"))
        self.assertEqual(Field.union(Field("a"), Field("a")), Field("a"))

    def test_union_different_names(self):
        self.assertEqual(Field.union(Field("a"), Field("b")), Field("a"))
        self.assertEqual(Field.union(Field("b"), Field("a")), Field("b"))

    def test_union_same_type(self):
        self.assertEqual(Field.union(Field("a"), Field("a")), Field("a"))

        for t in Field.TYPES:
            self.assertEqual(Field.union(Field("a", t), Field("a", t)), Field("a", t))

    def test_union_different_types(self):
        self.assertEqual(Field.union(Field("a", Field.TYPES.STRING), Field("a")), Field("a"))
        self.assertEqual(Field.union(Field("a", Field.TYPES.NUMBER), Field("a")), Field("a"))
        self.assertEqual(Field.union(Field("a", Field.TYPES.STRING), Field("a", Field.TYPES.NUMBER)), Field("a", Field.TYPES.STRING))

    def test_union_error(self):
        with self.assertRaises(ValueError):
            Field.union()


class TestSubheader(unittest.TestCase):
    def test_str(self):
        self.assertEqual(str(Subheader("key", "value")), "KEY:value")
        self.assertEqual(str(Subheader("order", "a:asc b:desc")), "ORDER:a:asc b:desc")

    def test__eq__(self):
        self.assertEqual(Subheader("key", "value"), Subheader("KEY", "value"))
        self.assertNotEqual(("key", "value"), Subheader("order", "a:asc b:desc"))

    def test__eq__inherited(self):
        class SubheaderChild(Subheader):
            pass

        subheader_child1 = SubheaderChild("key", "value")
        subheader_child2 = SubheaderChild("key", "value")

        self.assertEqual(subheader_child1, subheader_child2)
        self.assertNotEqual(Subheader("key", "value"), subheader_child1)

    def test_parse(self):
        self.assertEqual(Subheader.parse("key:value"), Subheader("key", "value"))
        self.assertEqual(Subheader.parse("ORDER:a:asc b:desc"), Subheader("order", "a:asc b:desc"))

    def test_parse_incorrect(self):
        Subheader.parse("key:value")
        with self.assertRaises(ValueError):
            Subheader.parse("key value")

    def test_union(self):
        self.assertEqual(Subheader.union(
            Subheader("k", "v1"),
            Subheader("k", "v2")
        ), Subheader("k", "?"))

    def test_union_error(self):
        with self.assertRaises(ValueError):
            Subheader.union()

        with self.assertRaises(ValueError):
            Subheader.union(
                Subheader("k1", "v"),
                Subheader("k2", "v")
            )


class TestSubheaderCount(unittest.TestCase):
    def test_init_value(self):
        subheader1 = SubheaderCount("count", 1)
        subheader2 = SubheaderCount("count", "1")
        self.assertEqual(subheader1.value, 1)
        self.assertEqual(subheader2.value, 1)
        self.assertEqual(subheader1, subheader2)

    def test_merge(self):
        self.assertEqual(SubheaderCount.union(
            SubheaderCount("count", 1),
            SubheaderCount("count", 2)
        ), SubheaderCount("count", 3))


class TestHeader(unittest.TestCase):
    def setUp(self):
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

        self.assertEqual(str(header), "a:num\tb:str\tc #COUNT:1 #ORDER:a:asc")

        header.delimiter = ','
        self.assertEqual(str(header), "a:num,b:str,c #COUNT:1 #ORDER:a:asc")

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
        self.assertEqual(header1, header2)

        header2.fields=self.fields[1:]
        self.assertNotEqual(header1, header2)

        header2.fields=self.fields[1:2] + self.fields[0:1] + self.fields[2:]
        self.assertNotEqual(header1, header2)

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

        self.assertNotEqual(header1, header2)

        header2.subheaders=self.subheaders[1:] + self.subheaders[0:1]
        self.assertEqual(header1, header2)

    def test_generate(self):
        self.assertEqual("f0,f1,f2", str(Header.generate(',', 3)))

    def test_parse(self):
        self.assertEqual(Header.parse("a:num\tb:str\tc #COUNT:1 #ORDER:a:asc"), Header(
            delimiter='\t',
            fields=self.fields,
            subheaders=self.subheaders
        ))
        
        self.assertEqual(Header.parse("a:num,b:str,c #COUNT:1 #ORDER:a:asc"), Header(
            delimiter=',',
            fields=self.fields,
            subheaders=self.subheaders
        ))

        self.assertEqual(Header.parse("a:num|b:str|c #COUNT:1 #ORDER:a:asc", delimiter="|"), Header(
            delimiter='|',
            fields=self.fields,
            subheaders=self.subheaders
        ))

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
        self.assertEqual(Header.union(h1, h2), expected)


if __name__ == '__main__':
    unittest.main()
