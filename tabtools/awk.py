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
import time


class AWKProgram(object):
    def __init__(self, fields, filters=None, output_expressions=None):
        """ Awk Program generator.

        Params
        ------
        fields: tabtools.base.DataDescription.fields
        output_expressions: list, optional
        filters: list, optional

        """
        self.fields = fields
        self.filters = filters or []
        self.output_expression = output_expressions or []
        self.context = {
            field.title: '${}'.format(index + 1)
            for index, field in enumerate(self.fields)
        }

    def __str__(self):
        return "'{print $1, $2}'"

    @classmethod
    def get_moving_average_template(cls, window_size):
        """ Generates template for moving agerage for given window size.

        template = get_moving_average_template(2)
        program = template.format(output, input)

        Example output for window_size = 5
        --------------

        __ma5_mod = NR % 5;
        if(NR > 5){__ma5_sum_<timestamp> -= __ma5_array_<timestamp>[__ma5_mod]};
        sum+={1};
        __ma5_array[mod]={1};
        {0} = sum/count;

        """
        timestamp = "{:.5f}".format(time.time()).replace('.', '')
        output = "__ma{size}_mod = NR % {size}; if(NR > {size}) {{{{" +\
            "__ma{size}_sum_{timestamp} -= __ma{size}_array_{timestamp}" +\
            "[__ma{size}_mod]}}}}; __ma{size}_sum_{timestamp} += {_in};" +\
            "__ma{size}_array_{timestamp}[__ma{size}_mod] = {_in};" +\
            "{_out} = __ma{size}_sum_{timestamp} / {size};"

        output = output.format(
            size=window_size, timestamp=timestamp, _in='{1}', _out='{0}')
        return output


class AWKNodeVisitor(ast.NodeVisitor):
    def generic_visit(node):
        raise ValueError("Class is not supported {}".format(node))
