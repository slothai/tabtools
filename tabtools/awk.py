""" Tools to generate awk code to be executed.

awk - the most common and will be found on most Unix-like systems, oldest
version and inferior to newer ones.

mawk - fast AWK implementation which it's code base is based on
a byte-code interpreter.

nawk - while the AWK language was being developed the authors released
a new version (hence the n - new awk) to avoid confusion. Think of it like
the Python 3.0 of AWK.

gawk - abbreviated from GNU awk. The only version in which the developers
attempted to add i18n support. Allowed users to write their own C shared
libraries to extend it with their own "plug-ins". This version is the standard
implementation for Linux, original AWK was written for Unix v7.

"""
import ast
import copy
import time


class AWKProgram(object):
    def __init__(self, fields, filters=None, output_expressions=None):
        """ Awk Program generator.

        Params
        ------
        fields: tabtools.base.DataDescription.fields
        output_expressions: list, optional
        filters: list, optional

        context: dict
            title -> (index, [type]), if there is no type, str is used.

        """
        self.fields = fields
        self.filters = filters or []
        self.output_expressions = output_expressions or []
        self.context = {
            field.title: Expression('${}'.format(index + 1), title=field.title)
            for index, field in enumerate(self.fields)
        }
        self.output = Expression.from_str(
            "; ".join(self.output_expressions),
            self.context
        )

    def __str__(self):
        result = "'{\n"
        result += "".join(["{};\n".format(str(o)) for o in self.output])
        result += "print " + ", ".join([
            o.title for o in self.output
            if o.title and not o.title.startswith('_')
        ])
        result += "\n}'"
        return result


class Expression(ast.NodeTransformer):

    """ Expression class.

    Class is used to control expression types

    """

    def __init__(self, value, title=None, _type=None, context=None):
        self.title = title
        self._type = _type
        self.value = value
        self.context = context or {}

    def __str__(self):
        if self.title is not None:
            return "{} = {}".format(self.title, self.value)
        else:
            return str(self.value)

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.value)

    @classmethod
    def from_str(cls, value, context=None):
        obj = cls(None, context=context)
        expressions =  obj.visit(ast.parse(value))
        return expressions

    def generic_visit(self, node):
        raise ValueError("Class is not supported {}".format(node))

    def visit_Module(self, node):
        """ Expected input

        Assignment
        Expression which is variable

        """
        output = []
        for statement in node.body:
            if not isinstance(statement, (ast.Expr, ast.Assign)):
                raise ValueError("Incorrect input {}".format(statement))

            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Name):
                statement = ast.Assign(
                    targets=[statement.value], value=statement.value)

            output.extend(self.visit(statement))
        return output

    def visit_Assign(self, node):
        """ Return list of expressions.

        in case of code x = F(expr), generate two expressions
        __var = expr
        x = F(__var)

        """
        target_name = node.targets[0].id
        values = self.visit(node.value)
        if target_name not in self.context:
            # add variable to context, it is already defined, {'var': 'var'}
            self.context[target_name] = Expression(target_name)
        values[-1].title = target_name
        return values

    def visit_Name(self, node):
        if node.id in self.context:
            return [self.context[node.id]]
        else:
            raise ValueError("Variable {} not in context".format(node.id))

    def visit_BinOp(self, node):
        options = {
            ast.Add: '+',
            ast.Sub: '-',
            ast.Mult: '*',
            ast.Pow: '**',
            ast.Div: '/'
        }
        op = type(node.op)
        if op in options:
            output = []
            lefts = self.visit(node.left)
            rights = self.visit(node.right)

            for left in lefts[:-1]:
                output.append(left)
                self.context.update(left.context)

            for right in rights[:-1]:
                output.append(right)
                self.context.update(right.context)

            expr = Expression(
                "({}) {} ({})".format(
                    lefts[-1].value,
                    options[op],
                    rights[-1].value
                ),
                context=self.context
            )
            output.append(expr)
            return output
        else:
            raise ValueError("Not Supported binary operation {}".format(op.__name__))

    def visit_Num(self, node):
        return [Expression(node.n)]

    def visit_Call(self, node):
        """ Substitute function.
        F(expression) -> __val_1 = expression, __val_2 = F(__val_1)
        """
        output = []
        for arg in node.args:
            var = "__var_{}".format(len(self.context))
            visited_args = self.visit(arg)

            # NOTE: deepcopy possible existing in context expression, do not
            # overwrite original title to not affect previous expression.
            # NOTE: if it is ok to use previous expressions in current
            # function, then lines until output.extend(..) could be removed.
            # But in this case duplicates in generated code could be found.
            val = copy.deepcopy(visited_args[-1])
            val.title = var
            self.context[var] = val
            visited_args[-1] = val
            output.extend(visited_args)

        # Built-in awk functions
        var = "__var_{}".format(len(self.context))

        try:
            transform_function = getattr(
                self, "transform_{}".format(node.func.id))
        except AttributeError:
            expression = Expression(
                "{func}({args})".format(func=node.func.id, args=" ,".join([
                    o.title for o in output
                ])), title=var, context=self.context
            )
        else:
            code = transform_function(var, output)
            # NOTE: dont add title to expression, it would assing generic
            # fuction code to it, which might cause problems with that
            # function.
            expression = Expression(code, context=self.context)

        self.context[var] = expression
        output.append(expression)
        output.append(Expression(var, title=var))
        return output

    def transform_AVG(self, output, inputs):
        """ Transform function call into awk program."""
        value = inputs[0].title
        code = "NR == 1 ? {output} = {value} : {output} = ((NR - 1) *" +\
            " {output} + {value}) / NR"
        code = code.format(output=output, value=value)
        return code

    def transform_SMA(self, output, inputs):
        """ Transform simple moving average.

        inputs: param and window size.

        Usage:
            x = SMA(a, 5)

        __ma_mod = NR % 5;
        __ma_sum += $1;
        __ma_array[__ma_mod] = $1;
        $output = null;
        if(NR > 5){
            __ma_sum -= __ma_array[__ma_mod]
            $output = __ma_sum / 5;
        }

        """
        value = inputs[0].title
        window_size = int(inputs[1].value)
        code = """__ma_mod{size} = NR % {size}
__ma_sum{size} += {value}
if(NR > {size}) {{
    __ma_sum{size} -= __ma_array{size}[__ma_mod{size}]
    {output} = __ma_sum{size} / {size}
}} else {{
    {output} = ""
}}
__ma_array{size}[__ma_mod{size}] = {value}"""
        code = code.format(output=output, value=value, size=window_size)
        return code

    def transform_EMA(self, output, inputs):
        """ Transform exponential moving average.

        inputs: param, window size, alpha (optional)
        alpha default = 2 / (1 + window_size)
        it is possible to set alpha = 3 / (1 + window_size) in this case
        in the first N elements there is 1 - exp(-3) = 95% of tatal weight.

        Usage:
            x = EMA(a, 5)

        __alpha = {alpha}
        NR == 1 ? {output} = {value} :
            {output} = {alpha} * {value} + (1 - {alpha}) * {output}"

        """
        value = inputs[0].title
        window_size = int(inputs[1].value)
        if len(inputs) > 2:
            alpha = inputs[2].value
        else:
            alpha = 2.0 / (1 + window_size)

        code = """NR == 1 ? {output} = {value} : {output} = {alpha} * {value} + {beta} * {output}"""  # nolint
        code = code.format(
            output=output, value=value, alpha=alpha, beta=1-alpha)
        return code
