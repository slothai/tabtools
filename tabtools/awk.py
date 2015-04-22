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

from .utils import Choices


class AWKProgram(object):

    """ AWK program generator.

    Supports group function and modules

    Supported functions:
        SUM(x): sum of elements in column x
        SUM(x, k): sum of last k elements in column x
        SUM2(x): sum of squares of elements in column x
        AVG(x): average value of elements in column x
        AVG(x, k): moving average of last k elements in column x
        EMA(x, k): exponential moving average with a = 2 / (k + 1)
        MAX(x): maximum value in column x
        MAX(x, k): moving maximum of last k elements in x
        MIN(x): minimum value in column x
        MIN(x, k): moving minimum of last k elements in x
        EPOCH(x): convert date from iso to timestamp
    """

    MODULES = Choices(
        ("dequeue", "DEQUE"),
    )

    def __init__(self, fields, filters=None, output_expressions=None,
                 group_key=None, group_expressions=None):
        """ Awk Program generator.

        Params
        ------
        fields: tabtools.base.DataDescription.fields
        output_expressions: list, optional
        filters: list, optional

        context: dict
            title -> (index, [type]), if there is no type, str is used.

        Program structure
        -----------------
        <modules>
        BEGIN{
            <init>
        }{
            <main part>
        }END{
            <final part>
        }

        _NR local line number.
        If program has group functionality, it star
        If program does not have group functionality, it equals to NR

        """
        self.fields = fields
        self.filters = filters or []
        self.output_expressions = output_expressions or []
        self.group_expressions = group_expressions or []
        self.context = {
            field.title: Expression('${}'.format(index + 1), title=field.title)
            for index, field in enumerate(self.fields)
        }

        if group_key:
            self.key = Expression.from_str(group_key, self.context)
            self.key[-1].title = "__group_key"
            self.context["__group_key"] = self.key[-1]

            self.group = Expression.from_str(
                "; ".join(self.group_expressions), self.context)

        self.output = Expression.from_str(
            "; ".join(self.output_expressions),
            self.context
        )

    def __str__(self):
        result = "'\n"
        result += self.modules_code
        result += "{\n"
        # result += self.group_code
        result += "\n"
        result += self.output_code
        result += "\n}'"
        return result

    @property
    def modules_code(self):
        """ Get code for modules used.

        Expression might use modules or functions, such as queue or dequeue.
        Iterate over all of the expressions and collect modules from them.

        """
        modules = set([])
        for expression in self.output:
            modules |= expression.modules

        if self.group_key:
            for expression in self.key + self.group:
                modules |= expression.modules

        return "\n".join([getattr(self, "module_{}".format(module))
                          for module in self.modules])

    @property
    def output_code(self):
        result = "".join(["{};\n".format(str(o)) for o in self.output])
        result += "print " + ", ".join([
            o.title for o in self.output
            if o.title and not o.title.startswith('_')
        ])
        return result

    @property
    def group_code(self):
        """ Get code of grouping part."""
        result = "\n".join(str(k) for k in self.key)
        group_code = """\nif(NR == 1){{
    # Update group expressions
{group}
{output_code}
}} else {{

}}"""
        group_code = group_code.format(
            group="".join(["    {};\n".format(str(o)) for o in self.group if str(o)]),
            output_code=self.output_code
        )
        result += group_code
        return result

    @property
    def module_dequeue(self):
        """ Deque realizsation in awk."""
        return """# awk module degue
function deque_init(d) {d["+"] = d["-"] = 0}
function deque_is_empty(d) {return d["+"] == d["-"]}
function deque_push_back(d, val) {d[d["+"]++] = val}
function deque_push_front(d, val) {d[--d["-"]] = val}
function deque_back(d) {return d[d["+"] - 1]}
function deque_front(d) {return d[d["-"]]}
function deque_pop_back(d) {if(deque_is_empty(d)) {return NULL} else {i = --d["+"]; x = d[i]; delete d[i]; return x}}
function deque_pop_front(d) {if(deque_is_empty(d)) {return NULL} else {i = d["-"]++; x = d[i]; delete d[i]; return x}}
function deque_print(d){x="["; for (i=d["-"]; i<d["+"] - 1; i++) x = x d[i]", "; print x d[d["+"] - 1]"]; size: "d["+"] - d["-"] " [" d["-"] ", " d["+"] ")"}
"""


class Expression(ast.NodeTransformer):

    """ Expression class.

    Class is used to control expression types

    """

    def __init__(self, value, title=None, _type=None,
                 context=None, begin=None):
        """ Expression init.

        value: formula to use
        title: optional variable to assign
        begin: initial value

        """
        self.title = title
        self._type = _type
        self.value = value
        self.begin = begin
        self.context = context or {}
        self.modules = set({})

    def __str__(self):
        if self.title is not None:
            return "{} = {}".format(self.title, self.value)
        else:
            return str(self.value)

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.value)

    @classmethod
    def from_str(cls, value, context=None):
        expressions = cls(None, context=context).visit(ast.parse(value))
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

            if isinstance(statement, ast.Expr):
                if isinstance(statement.value, ast.Name):
                    statement = ast.Assign(
                        targets=[statement.value], value=statement.value)
                else:
                    raise ValueError("Incorrect input {}".format(statement))

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

    def visit_UnaryOp(self, node):
        options = {
            ast.USub: '-',
        }
        op = type(node.op)
        if op in options:
            output = self.visit(node.operand)
            self.context.update(output[-1].context)

            expr = Expression(
                "{}{}".format(options[op], output[-1].value),
                context=self.context)
            output.append(expr)
            return output
        else:
            raise ValueError("Not Supported unary operation {}".format(op.__name__))

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

    def visit_Expr(self, node):
        return self.visit(node.value)

    def _get_suffix(self):
        """ Get unique suffix for variables insude the function."""
        return "_{}".format(int(time.time() * 10 ** 6))

    def transform_SUM(self, output, inputs):
        code = "{o} += {v}".format(o=output, v=inputs[0].title)
        expression = Expression(code, context=self.context)
        return expression

    def transform_SUM2(self, output, inputs):
        """ Sum of squares."""
        code = "{o} += {v} ** 2".format(o=output, v=inputs[0].title)
        expression = Expression(code, context=self.context)
        return expression

    def transform_AVG(self, output, inputs):
        """ Transform function call into awk program."""
        value = inputs[0].title
        code = "NR == 1 ? {output} = {value} : {output} = ((NR - 1) *" +\
            " {output} + {value}) / NR"
        code = code.format(output=output, value=value)
        expression = Expression(code, context=self.context)
        return expression

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
        suffix = self._get_suffix()
        code = """__ma_mod{suffix} = NR % {size}
__ma_sum{suffix} += {value}
if(NR > {size}) {{
    __ma_sum{suffix} -= __ma_array{suffix}[__ma_mod{suffix}]
    {output} = __ma_sum{suffix} / {size}
}} else {{
    {output} = ""
}}
__ma_array{suffix}[__ma_mod{suffix}] = {value}"""
        code = code.format(output=output, value=value,
                           size=window_size, suffix=suffix)
        return code

    def transform_EMA(self, output, inputs):
        """ Transform exponential moving average.

        inputs: param, window size, alpha (optional)
        alpha default = 2 / (1 + window_size)
        it is possible to set alpha = 3 / (1 + window_size) in this case
        in the first N elements there is 1 - exp(-3) = 95% of tatal weight.

        Usage:
            x = EMA(a, 5)

        NR == 1 ? {output} = {value} :
            {output} = {alpha} * {value} + (1 - {alpha}) * {output}"

        """
        value = inputs[0].title
        window_size = int(inputs[1].value)
        if len(inputs) > 2:
            alpha = inputs[2].value
        else:
            alpha = 2.0 / (1 + window_size)

        code = "{output} = (NR == 1 ? {value} : {alpha} * {value} + {beta} * {output})"  # nolint
        code = code.format(
            output=output, value=value, alpha=alpha, beta=1-alpha)
        return code

    def transform_Prev(self, output, inputs):
        """ Previous value of input"""
        value = inputs[0].title
        suffix = self._get_suffix()
        code = "{output} = (NR == 1 ? 0 : prev{suffix}); prev{suffix} = {value}"
        code = code.format(output=output, value=value, suffix=suffix)
        return code

    def _transform_MinMax(self, output, inputs, comparison=None):
        """
        Two deques with values and indexes: dv and di
        comparison: ">" -> Max, "<" -> Min
        """
        if not (1 <= len(inputs) <= 2):
            raise ValueError("Function should have 1 or 2 arguments")

        value = inputs[0].title
        if len(inputs) == 1:
            code = "{o} = (NR == 1 ? {v} : ({v} {c} {o} ? {v}: {o}))".format(
                o=output, v=value, c=comparison)
            return code

        window_size = int(inputs[1].value)
        suffix = self._get_suffix()
        code = """if(NR == 1){{deque_init(dv{suffix}); deque_init(di{suffix})}}
while(!deque_is_empty(dv{suffix}) && {value} {c}= deque_back(dv{suffix})) {{deque_pop_back(dv{suffix}); deque_pop_back(di{suffix})}}
if (NR > {size}) {{
    while(!deque_is_empty(dv{suffix}) && deque_front(di{suffix}) <= NR - {size}) {{deque_pop_front(dv{suffix}); deque_pop_front(di{suffix})}}
}}
deque_push_back(dv{suffix}, {value}); deque_push_back(di{suffix}, NR)
{output} = deque_front(dv{suffix})
"""
        code = code.format(
            output=output, value=value, size=window_size,
            suffix=suffix, c=comparison
        )
        return code

    def transform_Min(self, output, inputs):
        return self._transform_MinMax(output, inputs, comparison="<")

    def transform_Max(self, output, inputs):
        return self._transform_MinMax(output, inputs, comparison=">")

    def transform_Sum(self, output, inputs):
        code = "{output} = (NR == 1 ? {value} : {output} + {value})".format(
            output=output, value=inputs[0].title)
        return code

    def transform_max(self, output, inputs):
        # FIXME: check input, validate, clean.
        code = "{output} = ({a} > {b} ? {a}: {b})".format(
            output=output, a=inputs[0].title, b=inputs[1].title)
        return code

    def transform_DateEpoch(self, output, inputs):
        value = inputs[0].title
        suffix = self._get_suffix()
        code = """split({v}, __date{suffix}, "-"); {o} = mktime(__date{suffix}[1]" "__date{suffix}[2]" "__date{suffix}[3]" 00 00 00 UTC")"""
        code = code.format(o=output, v=value, suffix=suffix)
        return code

    # Group Expressions
    def transform_First(self, output, inputs):
        return ""

    def transform_Last(self, output, inputs):
        return "{o} = {v}".format(o=output, v=inputs[0].title)
