""" Scripts of tool."""
import argparse
import itertools
import tempfile
import sys

from .base import OrderedField, DataDescription, Field
from .files import FileList
from .awk import Expression, AWKProgram


def cat():
    """ cat function.

    tact file1, file2

    """
    parser = argparse.ArgumentParser(
        add_help=True,
        description="Concatenate files and print on the standard output"
    )
    parser.add_argument(
        'files', metavar='FILE', type=argparse.FileType('r'), nargs="*")
    args = parser.parse_args()
    files = FileList(args.files)
    sys.stdout.write(files.header + '\n')
    sys.stdout.flush()
    files("cat")


def srt():
    """ sort function.

    tsrt -k field1 -k field2 file1

    """
    parser = argparse.ArgumentParser(
        add_help=True,
        description="Sort lines of text files"
    )
    parser.add_argument(
        'files', metavar='FILE', type=argparse.FileType('r'), nargs="*")
    parser.add_argument('-k', '--keys', action="append", default=[])
    args = parser.parse_args()
    files = FileList(args.files)
    fields = [f.title for f in files.description.fields]
    order = [OrderedField.parse(key) for key in args.keys]
    options = [
        "-k{0},{0}{1}{2}".format(
            fields.index(f.title) + 1, f.sort_type, f.sort_order)
        for f in order
    ]
    sys.stdout.write(files.header + '\n')
    sys.stdout.flush()
    files("sort", *options)


def awk():
    parser = argparse.ArgumentParser(
        add_help=True,
        description="Perform a map operation on all FILE(s)"
        "and write result to standard output."
    )
    parser.add_argument(
        'files', metavar='FILE', type=argparse.FileType('r'), nargs="*")
    parser.add_argument('-o', '--output', action="append", help="Output fields",
        default=[])
    parser.add_argument('-f', '--filter', action="append", help="Filter expression")
    args = parser.parse_args()
    files = FileList(args.files)
    program = AWKProgram(files.description.fields, args.filter, args.output)

    # sys.stdout.write("%s\n" % program)
    description = DataDescription([
        Field(o.title, o._type) for o in program.output
    ])
    sys.stdout.write(str(description) + '\n')
    sys.stdout.flush()
    files('awk', '-F', '"\t"', '-v', 'OFS="\t"', str(program))


def pretty():
    """ Prettify output.

    Uses sys.stdin only
    tcat file | tpretty

    """
    header = sys.stdin.readline()
    fields = DataDescription.parse(header).fields
    column_widths = [len(str(field)) for field in fields]

    file_name = tempfile.mkstemp()[1]
    with open(file_name, 'w') as f:
        for line in sys.stdin:
            for findex, field in enumerate(line.rstrip('\n').split()):
                column_widths[findex] = max(column_widths[findex], len(field))
            f.write(line)

    column_widths = [x + 2 for x in column_widths]
    print("|".join([
        (" {} ".format(str(f))).ljust(x)
        for x, f in itertools.izip(column_widths, fields)
    ]))
    print("+".join(["-" * x for x in column_widths]))
    with open(file_name, 'r') as f:
        for line in f:
            print("|".join([
                (" {} ".format(str(field))).ljust(x)
                for x, field in itertools.izip(
                    column_widths, line.rstrip('\n').split()
                )
            ]))
