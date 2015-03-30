""" Scripts of tool."""
import argparse
import itertools

from .base import OrderedField
from .files import FileList


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
    files("sort", *options)


def pretty():
    """ Prettify output.

    tpretty file
    tcat file | tpretty

    """
    parser = argparse.ArgumentParser(
        add_help=True,
        description="Prettify files and print on the standard output"
    )
    parser.add_argument(
        'files', metavar='FILE', type=argparse.FileType('r'), nargs="*")
    args = parser.parse_args()
    files = FileList(args.files)
    description = files.description
    column_width = [len(str(f)) for f in description.fields]

    for f in files:
        for lindex, line in enumerate(f.fd):
            if lindex == 0:
                continue
            for findex, field in enumerate(line.rstrip('\n').split()):
                column_width[findex] = max(column_width[findex], len(field))

    column_width = [x + 2 for x in column_width]
    print("|".join([
        (" {} ".format(str(f))).ljust(x)
        for x, f in itertools.izip(column_width, description.fields)
    ]))
    print("+".join(["-" * x for x in column_width]))
    for f in files:
        f.fd.seek(0)
        for lindex, line in enumerate(f.fd):
            if lindex == 0:
                continue
            print("|".join([
                (" {} ".format(str(field))).ljust(x)
                for x, field in itertools.izip(
                    column_width, line.rstrip('\n').split()
                )
            ]))
