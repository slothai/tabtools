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
        expression = "x; a = AVG(x)"
        context = dict(x=Expression('$1', 'x'))
        output = Expression.from_str(expression, context)
        self.assertEqual(
            "; ".join([str(o) for o in output]),
            "x = $1; __var_1 = $1; " +
            "NR == 1 ? __var_2 = __var_1 : __var_2 " +
            "= ((NR - 1) * __var_2 + __var_1) / NR; a = __var_2"
        )

    def test_transform_simple_moving_average(self):
        expression = "a = SMA(x, 5)"
        context = dict(x=Expression('$1', 'x'))
        output = Expression.from_str(expression, context)
        self.assertEqual(
            "; ".join([str(o) for o in output]),
            '__var_1 = $1; __var_2 = 5; __ma_mod5 = NR % 5\n' +
            '__ma_sum5 += __var_1\nif(NR > 5) {\n    ' +
            '__ma_sum5 -= __ma_array5[__ma_mod5]\n    ' +
            '__var_3 = __ma_sum5 / 5\n} else {\n    ' +
            '__var_3 = ""\n}\n__ma_array5[__ma_mod5] = __var_1; a = __var_3'
        )

    def test_transform_exponential_moving_average(self):
        expression = "a = EMA(x, 7)"
        context = dict(x=Expression('$1', 'x'))
        output = Expression.from_str(expression, context)
        self.assertEqual(
            "; ".join([str(o) for o in output]),
            "__var_1 = $1; __var_2 = 7; NR == 1 ? __var_3 = __var_1 : " +
            "__var_3 = 0.25 * __var_1 + 0.75 * __var_3; a = __var_3"
        )

    def test_transform_max_moving_average(self):
        expression = "a = Max(x, 3)"
        context = dict(x=Expression('$1', 'x'))
        output = Expression.from_str(expression, context)
        self.assertEqual(
            "; ".join([str(o) for o in output]),
            ""
        )
