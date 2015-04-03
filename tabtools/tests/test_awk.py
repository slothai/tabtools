import unittest
import ast

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
        self.assertEqual(output[0].value, '$1 + 1')

    def test_simple_expressions2(self):
        expression = "a = x + 1; b = 1 + 1; c = a * 2"
        context = dict(x=Expression('$1', 'x'))
        output = Expression.from_str(expression, context)
        self.assertEqual(str(output[0]), 'a = $1 + 1')
        self.assertEqual(str(output[1]), 'b = 1 + 1')
        self.assertEqual(str(output[2]), 'c = a * 2')
