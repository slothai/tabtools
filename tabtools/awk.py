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


class AWKBaseProgram(object):

    """ AWK program generator."""

    MODULES = Choices(
        ("dequeue", "DEQUE"),
    )

    def __str__(self):
        result = "'\n"
        result += self.modules_code

        if self.begin_code:
            result += "\nBEGIN{{\n{}\n}}\n".format(self.begin_code)

        result += "{\n"
        result += self.output_code
        result += "\n}'"
        return result

    @property
    def begin_code(self):
        return "\n".join([
            expression.begin for expression in self.output
            if expression.begin])

    @property
    def modules_code(self):
        """ Get code for modules used.

        Expression might use modules or functions, such as queue or dequeue.
        Iterate over all of the expressions and collect modules from them.

        """
        modules = set([])
        for expression in self.output:
            modules |= expression.modules

        # if self.group_key:
            # for expression in self.key + self.group:
                # modules |= expression.modules

        return "\n".join([
            getattr(self, "module_{}".format(module))
            for module in modules])

    @property
    def module_dequeue(self):
        """ Deque realizsation in awk."""
        return "\n".join([
            '# awk module degue',
            'function deque_init(d) {d["+"] = d["-"] = 0}',
            'function deque_is_empty(d) {return d["+"] == d["-"]}',
            'function deque_push_back(d, val) {d[d["+"]++] = val}',
            'function deque_push_front(d, val) {d[--d["-"]] = val}',
            'function deque_back(d) {return d[d["+"] - 1]}',
            'function deque_front(d) {return d[d["-"]]}',
            'function deque_pop_back(d) {if(deque_is_empty(d)) {return NULL} else {i = --d["+"]; x = d[i]; delete d[i]; return x}}',  # nolint
            'function deque_pop_front(d) {if(deque_is_empty(d)) {return NULL} else {i = d["-"]++; x = d[i]; delete d[i]; return x}}',  # nolint
            'function deque_print(d){x="["; for (i=d["-"]; i<d["+"] - 1; i++) x = x d[i]", "; print x d[d["+"] - 1]"]; size: "d["+"] - d["-"] " [" d["-"] ", " d["+"] ")"}',  # nolint
        ])


class AWKStreamProgram(AWKBaseProgram):

    """ AWK stream processor.

    Params
    ------
    fields: tabtools.base.DataDescription.fields
    output_expressions: list, optional
    filter_expressions: list, optional

    context: dict
        title -> (index, [type]), if there is no type, str is used.

    Program structure
    -----------------
        <modules>
        BEGIN{
            <init>
        }
        {
            <main part>
        }

    """

    def __init__(self, fields, filter_expressions=None, output_expressions=None):
        self.fields = fields
        self.filter_expressions = filter_expressions or []
        self.output_expressions = output_expressions or []
        self.context = {
            field.title: Expression('${}'.format(index + 1), title=field.title)
            for index, field in enumerate(self.fields)
        }

        self.filters = StreamExpression.from_str(
            "; ".join(self.filter_expressions),
            self.context
        )
        self.output = StreamExpression.from_str(
            "; ".join(self.output_expressions),
            self.context
        )

    @property
    def output_code(self):
        result = ";\n".join([str(o) for o in self.output]) + ';\n'
        output_statement =  "print " + ", ".join([
            o.title for o in self.output
            if o.title and not o.title.startswith('_')
        ])
        if self.filters:
            # Wrap output expression with if statement
            result += "if({}) {{\n    {}\n}}".format(
                " && ".join([str(o) for o in self.filters]),
                output_statement
            )
        else:
            result += output_statement
        return result


class AWKGroupProgram(AWKBaseProgram):

    """ Awk Program generator.

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

    def __init__(self, fields, group_key, group_expressions):
        self.fields = fields
        self.context = {
            field.title: Expression('${}'.format(index + 1), title=field.title)
            for index, field in enumerate(self.fields)
        }

        self.key = Expression.from_str(group_key, self.context)
        # self.key[-1].title = "__group_key"
        self.key.append(Expression(self.key[-1].title, title="__group_key"))
        # self.context["__group_key"] = self.key[-1]

        self.group_expressions = group_expressions or []
        self.output = GroupExpression.from_str(
            "; ".join(self.group_expressions), self.context)

    def __str__(self):
        result = self.output_code
        return result

    @property
    def output_code(self):
        """ Get code of grouping part."""
        result = "'{\n"
        result += "\n".join(str(k) for k in self.key)
        result += "\n"
        group_code = "\n".join([
            "if(NR == 1){{",
            "    {group_init}",
            "}} else {{",
            "  if(__group_key != __group_key_previous){{",
            "    {group_finalize}",
            "    print __group_key_previous, {group_output}",
            "    {group_init}",
            "  }} else {{",
            "    {group_update}",
            "  }}",
            "}}",
            "__group_key_previous = __group_key;",
            "}}\nEND{{",
            "    {group_finalize}",
            "    print __group_key_previous, {group_output}",
        ])
        group_code = group_code.format(
            group_init="\n    ".join([
                str(o) if not o.begin else str(o.begin) for o in self.output
                if not (o.title and not o.title.startswith('_'))
            ]),
            group_update="\n    ".join([
                str(o) for o in self.output
                if not (o.title and not o.title.startswith('_'))
            ]),
            group_finalize="\n    ".join([
                str(o) for o in self.output
                if o.title and not o.title.startswith('_')
            ]),
            group_output=", ".join([
                o.title for o in self.output
                if o.title and not o.title.startswith('_')
            ])
        )
        result += group_code
        result += "\n}'"
        return result


class Expression(ast.NodeTransformer):

    """ Expression class.

    Class is used to control expression types

    Supported functions:
        EPOCH(x): convert date from iso to timestamp

    """

    def __init__(self, value, title=None, _type=None,
                 context=None, begin=None, modules=None):
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
        self.modules = set(modules or {})

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
                elif isinstance(statement.value, ast.Compare):
                    pass
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
            raise ValueError("Not Supported binary operation {}".format(
                op.__name__))

    def visit_BoolOp(self, node):
        options = {
            ast.And: '&&',
            ast.Or: '||',
        }
        op = type(node.op)
        vals = []
        if op in options:
            output = []

            for value in node.values:
                values = self.visit(value)

                for v in values[:-1]:
                    output.append(v)
                    self.context.update(v.context)

                vals.append(values[-1].value)

            expr = Expression(
                " {} ".format(options[op]).join([
                    "({})".format(v) for v in vals
                ]),
                context=self.context
            )
            output.append(expr)
            return output
        else:
            raise ValueError("Not Supported bool operation {}".format(
                op.__name__))


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
            raise ValueError("Not Supported unary operation {}".format(
                op.__name__))

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
            # NOTE: remove following duplicated arguments. They appear if
            # function has function as an argument:
            # f(x, g(y)) -> __var1 = x, __var2=y ....
            # f(__var1, __var2, __var2)  # strftime(%U, DateEpoch(x))
            args = []
            processed_args = set()

            for o in output:
                if o.title and o.title not in processed_args:
                    args.append(o.title)
                    processed_args.add(o.title)

            expression = Expression(
                "{func}({args})".format(
                    func=node.func.id,
                    args=", ".join(args)
                ), title=var, context=self.context
            )
        else:
            expression = transform_function(var, output)

        self.context[var] = expression
        output.append(expression)
        output.append(Expression(var, title=var))
        return output

    def visit_Expr(self, node):
        return self.visit(node.value)

    def visit_Str(self, node):
        return [Expression("\"{}\"".format(node.s), title=node.s)]

    def visit_IfExp(self, node):
        output = []
        tests = self.visit(node.test)
        bodys = self.visit(node.body)
        orelses = self.visit(node.orelse)

        output.extend(tests[:-1])
        output.extend(bodys[:-1])
        output.extend(orelses[:-1])
        expr = Expression(
            "({}) ? ({}) : ({})".format(
                tests[-1].value,
                bodys[-1].value,
                orelses[-1].value
            ),
            context=self.context
        )
        output.append(expr)
        return output

    def visit_Compare(self, node):
        options = {
            ast.Eq: '==',
            ast.NotEq: '!=',
            ast.Lt: '<',
            ast.LtE: '<=',
            ast.Gt: '>',
            ast.GtE: '>=',
        }
        lefts = self.visit(node.left)
        output = lefts[:-1]
        code = "({})".format(lefts[-1].value)
        for comparator, op in zip(node.comparators, node.ops):
            comparators = self.visit(comparator)
            output.extend(comparators[:-1])
            op = type(op)
            if op not in options:
                raise ValueError('Unknown comparator {}'.format(op))

            code += " {} ({})".format(options[op], comparators[-1].value)

        expr = Expression(code, context=self.context)
        output.append(expr)
        return output

    def _get_suffix(self):
        """ Get unique suffix for variables insude the function."""
        return "_{}".format(int(time.time() * 10 ** 6))

    def transform_DateEpoch(self, output, inputs):
        value = inputs[0].title
        code = "; ".join([
            'split({v}, __date{o}, "-")',
            '{o} = mktime(__date{o}[1]" "__date{o}[2]" "' +
            '__date{o}[3]" 00 00 00 UTC")',
        ]).format(o=output, v=value)
        expression = Expression(code, context=self.context)
        return expression


class StreamExpression(Expression):

    """ Exression management for stream operations.

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

    """

    def transform_SUM(self, output, inputs):
        """ Get sum or moving sum.

        Moving sum is calculated for lask k (inputs[1]) elements.
        Implementation is specific for awk: undefined variables equal to 0.
        Code is minified version of following:

        BEGIN {output = 0; array = [0, ..., 0]}
        mod = NR % k
        output = output + value
        if(NR > k){
            output = output - array[mod];  # remove old elements
        }
        array[mod] = value

        Modified version:
        mod = NR % k
        output += (value - array[mod])
        array[mod] = value

        """
        if len(inputs) > 2:
            raise ValueError("SUM function: too many arguments (>2)")

        value = inputs[0].title
        if len(inputs) == 1:
            code = "{o} += {v}".format(o=output, v=value)
        else:
            window_size = int(inputs[1].value)
            code = "; ".join([
                "__sum_mod{o} = NR % {size}",
                "{o} += ({v} - __sum_array{o}[__sum_mod{o}])",
                "__sum_array{o}[__sum_mod{o}] = {v}",
            ]).format(o=output, v=value, size=window_size)
        expression = Expression(code, context=self.context)
        return expression

    def transform_SUM2(self, output, inputs):
        """ Sum of squares."""
        code = "{o} += {v} ** 2".format(o=output, v=inputs[0].title)
        expression = Expression(code, context=self.context)
        return expression

    def transform_AVG(self, output, inputs):
        """ Get average or moving average.

        Moving average is calculated for lask k (inputs[1]) elements.
        Implementation is specific for awk: undefined variables equal to 0.
        Code is minified version of following:

        BEGIN {sum = 0; array = [0, ..., 0]}
        mod = NR % k
        sum = sum + value
        if(NR > k){
            sum = sum - array[mod];  # remove old elements
            output = sum / k
        } else {
            output = sum / NR
        }
        array[mod] = value

        Modified version:
            mod = NR % k
            sum += (value - array[mod])
            array[mod] = value
            output = sum / (NR > k ? k : NR)

        Average version initial code:
            if (NR == 1) {
                output = value
            } else {
                output = ((NR - 1) * output + value) / NR
            }
        Minified:
            o = (NR == 1 ? v : ((NR - 1) * {o} + {v}) / NR)
        Minified awk specific:
            o = ((NR - 1) * {o} + {v}) / NR

        """
        if len(inputs) > 2:
            raise ValueError("AVG function: too many arguments (>2)")

        value = inputs[0].title
        if len(inputs) == 1:
            code = "{o} = ((NR - 1) * {o} + {v}) / NR".format(
                o=output, v=value)
        else:
            window_size = int(inputs[1].value)
            code = "; ".join([
                "__sum_mod{o} = NR % {size}",
                "__sum{o} += ({v} - __sum_array{o}[__sum_mod{o}])",
                "__sum_array{o}[__sum_mod{o}] = {v}",
                "{o} = __sum{o} / (NR > {size} ? {size} : NR)",
            ]).format(o=output, v=value, size=window_size)

        expression = Expression(code, context=self.context)
        return expression

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
        if len(inputs) > 2:
            raise ValueError("EMA function: too many arguments (>2)")

        value = inputs[0].title
        window_size = int(inputs[1].value)
        if len(inputs) == 3:
            alpha = inputs[2].value
        else:
            alpha = 2.0 / (1 + window_size)

        code = "{o} = (NR == 1 ? {v} : {a} * {v} + {b} * {o})".format(
            o=output, v=value, a=alpha, b=1-alpha)
        expression = Expression(code, context=self.context)
        return expression

    def transform_PREV(self, output, inputs):
        """ Previous value of input"""
        value = inputs[0].title
        code = "{o} = prev{o}; prev{o} = {v}"
        # code = "{o} = prev{o}; prev{o} = {v}"
        code = code.format(o=output, v=value)
        expression = Expression(code, context=self.context)
        return expression

    def _transform_MinMax(self, output, inputs, comparison=None):
        """ Get Min/Max value.

        Works with both total and moving maximum/minimum.

        Parameters:
        -----------
        comparison: ">" -> Max, "<" -> Min

        Two deques with values and indexes: dv and di

        """
        if len(inputs) > 2:
            raise ValueError("Function should have 1 or 2 arguments")

        value = inputs[0].title
        if len(inputs) == 1:
            code = "{o} = ({v} {c} {o} || NR == 1 ? {v} : {o})".format(
                o=output, v=value, c=comparison)
            expression = Expression(code, context=self.context)
        else:
            window_size = int(inputs[1].value)
            begin = "deque_init(dv{o}); deque_init(di{o})".format(o=output)
            code = "\n".join([
                "while(!deque_is_empty(dv{o}) && {v} {c}= deque_back(dv{o})) {{",
                "  deque_pop_back(dv{o}); deque_pop_back(di{o})",
                "}}",
                "if (NR > {size}) {{",
                "  while(!deque_is_empty(dv{o}) && deque_front(di{o}) <= NR - {size}) {{",
                "    deque_pop_front(dv{o}); deque_pop_front(di{o})",
                "  }}\n}}",
                "deque_push_back(dv{o}, {v}); deque_push_back(di{o}, NR)",
                "{o} = deque_front(dv{o})"
            ]).format(
                o=output, v=value, size=window_size, c=comparison)

            expression = Expression(
                code, begin=begin, context=self.context,
                modules=[AWKBaseProgram.MODULES.DEQUE]
            )
        return expression

    def transform_MIN(self, output, inputs):
        return self._transform_MinMax(output, inputs, comparison="<")

    def transform_MAX(self, output, inputs):
        return self._transform_MinMax(output, inputs, comparison=">")

    def transform_max(self, output, inputs):
        # FIXME: check input, validate, clean.
        code = "{output} = ({a} > {b} ? {a}: {b})".format(
            output=output, a=inputs[0].title, b=inputs[1].title)
        expression = Expression(code, context=self.context)
        return expression


class GroupExpression(Expression):

    """ Expression for group operations."""

    def transform_FIRST(self, output, inputs):
        begin = "{o} = {v}".format(o=output, v=inputs[0].title)
        code = ""
        expression = Expression(code, begin=begin, context=self.context)
        return expression

    def transform_LAST(self, output, inputs):
        begin = "{o} = {v}".format(o=output, v=inputs[0].title)
        code = "{o} = {v}".format(o=output, v=inputs[0].title)
        expression = Expression(code, begin=begin, context=self.context)
        return expression

    def _transform_MinMax(self, output, inputs, comparison):
        begin = "{o} = {v}".format(o=output, v=inputs[0].title)
        code = "{o} = ({v} {c} {o} || NR == 1 ? {v} : {o})".format(
            o=output, v=inputs[0].title, c=comparison)
        expression = Expression(code, begin=begin, context=self.context)
        return expression

    def transform_MIN(self, output, inputs):
        return self._transform_MinMax(output, inputs, comparison="<")

    def transform_MAX(self, output, inputs):
        return self._transform_MinMax(output, inputs, comparison=">")

    def transform_SUM(self, output, inputs):
        begin = "{o} = {v}".format(o=output, v=inputs[0].title)
        code = "{o} += {v}".format(o=output, v=inputs[0].title)
        expression = Expression(code, begin=begin, context=self.context)
        return expression

    def transform_COUNT(self, output, inputs):
        begin = "{o} = 1".format(o=output)
        code = "{o}++".format(o=output)
        expression = Expression(code, begin=begin, context=self.context)
        return expression
