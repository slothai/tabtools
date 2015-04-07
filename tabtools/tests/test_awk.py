import unittest

from ..awk import Expression


class TestAWKNodeTransformer(unittest.TestCase):
    def test_constant(self):
        expression = "1"

        with self.assertRaises(ValueError):
            Expression.from_str(expression)

    def test_statement_field(self):
        expression = "a"
        context = dict()
        with self.assertRaises(ValueError):
            Expression.from_str(expression)
        context = dict(a=Expression('$1', 'a'))
        output = Expression.from_str(expression, context)
        self.assertEqual(output[0].value, '$1')
        self.assertEqual(output[0].title, 'a')
        self.assertEqual(str(output[0]), 'a = $1')

    def test_simple_expressions(self):
        expression = "a = x + 1"
        context = dict(x=Expression('$1', 'x'))
        output = Expression.from_str(expression, context)
        self.assertEqual(output[0].value, '($1) + (1)')

    def test_field_and_expression(self):
        expression = "a; b = a + 1"
        context = dict(a=Expression('$1', 'a'))
        output = Expression.from_str(expression, context)
        self.assertEqual(output[0].value, '$1')
        self.assertEqual(output[1].value, '($1) + (1)')

    def test_simple_expressions2(self):
        expression = "a = x + 1; b = 1 + 1; c = a * 2"
        context = dict(x=Expression('$1', 'x'))
        output = Expression.from_str(expression, context)
        self.assertEqual(str(output[0]), 'a = ($1) + (1)')
        self.assertEqual(str(output[1]), 'b = (1) + (1)')
        self.assertEqual(str(output[2]), 'c = (a) * (2)')

    def test_transform_function(self):
        expression = "a = exp(x + 1) + rand()"
        context = dict(x=Expression('$1', 'x'))
        output = Expression.from_str(expression, context)
        self.assertEqual(
            "; ".join([str(o) for o in output]),
            "__var_1 = ($1) + (1); __var_2 = exp(__var_1); " +
            "__var_3 = rand(); a = (__var_2) + (__var_3)"
        )

    def test_transform_function_predefined_ma(self):
        expression = "x; a = SMA(x)"
        context = dict(x=Expression('$1', 'x'))
        output = Expression.from_str(expression, context)
        self.assertEqual(
            "; ".join([str(o) for o in output]),
            "x = $1; __var_1 = $1; " +
            "__var_2 = NR == 1 ? __var_2 = __var_1 : __var_2 " +
            "= ((NR - 1) * __var_2 + __var_1) / NR; a = __var_2"
        )
