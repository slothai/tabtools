#!/usr/bin/env python3
""" Scripts of tool."""
import argparse
import os
from pipes import quote
import re
import subprocess
import sys
import tempfile
from distutils.spawn import find_executable
from itertools import zip_longest

from tabtools import __version__
from .base import Header, Field
from .files import FileList
from .awk import AWKStreamProgram, AWKGroupProgram

AWK_INTERPRETER = find_executable(os.environ.get('AWKPATH', 'awk'))

# see https://stackoverflow.com/questions/14207708/ioerror-errno-32-broken-pipe-python#answer-30091579
from signal import signal, SIGPIPE, SIG_DFL
signal(SIGPIPE, SIG_DFL)

def add_common_arguments(parser):
    parser.add_argument(
        '--version', action='version',
        version='%(prog)s {version}'.format(version=__version__))
    parser.add_argument(
        'files', metavar='FILE', type=argparse.FileType('r'), nargs="*")
    # If args.header is '' (default), get it from input files.
    # If header is None: deduce it from the input
    # If header is set, user whatever is set.
    parser.add_argument(
        '-H', '--header', nargs='?', default='', type=str,
        help="Header of the output data")
    parser.add_argument(
        '-N', '--no-header', action='store_true', help="Do not output header")
    return parser


def ttcat():
    """ cat function.

    tact file1, file2

    """
    parser = argparse.ArgumentParser(
        add_help=True,
        description="Concatenate files and print on the standard output"
    )
    add_common_arguments(parser)

    args = parser.parse_args()
    files = FileList(args.files, header_line=args.header)

    if not args.no_header:
        sys.stdout.write(str(files.header) + '\n')
        sys.stdout.flush()

    files("cat")


def tttail():
    parser = argparse.ArgumentParser(
        add_help=True,
        description="Tail files and print on the standard output"
    )
    parser.add_argument(
        'files', metavar='FILE', type=argparse.FileType('r'), nargs="*")
    parser.add_argument('-n', '--lines', default=10)
    add_common_arguments(parser)

    args = parser.parse_args()
    files = FileList(args.files, header_line=args.header)

    if not args.no_header:
        sys.stdout.write(files.header + '\n')
        sys.stdout.flush()

    command = "tail -q" + " -n{}".format(args.lines) if args.lines else ""
    files(command)


def ttsort():
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
    add_common_arguments(parser)

    args = parser.parse_args()
    files = FileList(args.files, header_line=args.header)


    fields = [f.title for f in files.header.fields]
    options = [
        '--field-separator=' + quote(files.header.delimiter),
    ] + [
        '-k{0},{0}'.format(fields.index(key) + 1) for key in args.keys
    ]

    if not args.no_header:
        sys.stdout.write(str(files.header) + '\n')
        sys.stdout.flush()

    files("sort", *options)


def ttmap():
    parser = argparse.ArgumentParser(
        add_help=True,
        description="Perform a map operation on all FILE(s)"
        "and write result to standard output.\n"
        "Current awk interpreter: '{}'."
        "To use specific AWK interpreter set AWKPATH environment variable:"
        "export AWKPATH=$(which mawk)".format(AWK_INTERPRETER)
    )
    parser.add_argument('-a', '--all-columns', action='store_true',
                        default=False,
                        help="Output all of the original columns first")
    # FIXME: does MUTABLE default=[] value affect the execution?
    parser.add_argument('-s', '--select', action="append",
                        help="Output fields", default=[])
    parser.add_argument('-w', '--where', action="append", default=[],
                        help="Filter expression")
    parser.add_argument('-v', '--variables', action="append", default=[],
                        help="Assigns value to program variable var")
    parser.add_argument('--debug', action='store_true', default=False,
                        help="Print result program")
    add_common_arguments(parser)

    args = parser.parse_args()
    files = FileList(args.files, header_line=args.header)

    select = args.select or ['*']
    if '*' in select:
        i = select.index('*')
        select = select[:i] + [f.title for f in files.header.fields] + select[i + 1:]

    program = AWKStreamProgram(
        files.header.fields,
        filter_expressions=args.where,
        output_expressions=select
    )

    if args.debug:
        sys.stdout.write("%s\n" % program)

    header = Header(
        delimiter=files.header.delimiter,
        fields=[
            Field(o.title, o._type) for o in program.output
            if o.title and not o.title.startswith('_')
        ]
    )

    if not args.no_header:
        sys.stdout.write(str(header) + '\n')
        sys.stdout.flush()

    files(AWK_INTERPRETER, '-F', quote(header.delimiter), '-v', 'OFS=' + quote(header.delimiter), str(program))


def ttreduce():
    parser = argparse.ArgumentParser(
        add_help=True,
        description="Perform a group operation on all FILE(s)"
        "and write result to standard output.\n"
        "Current awk interpreter: '{}'."
        "To use specific AWK interpreter set AWKPATH environment variable:"
        "export AWKPATH=$(which mawk).".format(AWK_INTERPRETER)
    )
    add_common_arguments(parser)
    parser.add_argument('-g', '--groupby', help="Group expression")
    parser.add_argument('-s', '--select', action="append",
                        default=[], help="Group expression")
    parser.add_argument('--debug', action='store_true', default=False,
                        help="Print result program")
    args = parser.parse_args()
    files = FileList(args.files)

    program = AWKGroupProgram(
        files.header.fields,
        group_key=args.groupby,
        group_expressions=args.select
    )

    if args.debug:
        sys.stdout.write("%s\n" % program)

    header = Header(
        delimiter=files.header.delimiter,
        fields=[
            Field(o.title, o._type) for o in program.key + program.output
            if o.title and not o.title.startswith('_')
        ]
    )

    if not args.no_header:
        sys.stdout.write(str(header) + '\n')
        sys.stdout.flush()

    files(AWK_INTERPRETER, '-F', quote(header.delimiter), '-v', 'OFS=' + quote(header.delimiter), str(program))


def ttpretty():
    """ Prettify output.

    Uses sys.stdin only
    tcat file | tpretty

    """
    DELIMITER = '\t'
    header = sys.stdin.readline()
    fields = Header.parse(header).fields
    column_widths = [len(str(field)) for field in fields]

    file_name = tempfile.mkstemp()[1]
    with open(file_name, 'w') as f:
        for line in sys.stdin:
            for findex, field in enumerate(line.rstrip('\n').split(DELIMITER)):
                column_widths[findex] = max(column_widths[findex], len(field))
            f.write(line)

    column_widths = [x + 2 for x in column_widths]
    print("|".join([
        (" {} ".format(str(_f))).ljust(x)
        for x, _f in zip(column_widths, fields)
    ]).rstrip())
    print("+".join(["-" * x for x in column_widths]))
    with open(file_name, 'r') as f:
        for line in f:
            print("|".join([
                (" {} ".format(str(field or ''))).ljust(x)
                for x, field in zip_longest(
                    column_widths, line.rstrip('\n').split(DELIMITER)
                )
            ]).rstrip())

    os.remove(file_name)


def ttplot():
    """ Use gnuplot with tab files.

    Usage
    -----
    cat file.tsv | tplot -e '<optional command>' script.gnu

    Input file should have name: '__input'
    Fields should start with: '__', for example instead of a use __a.

    Examples
    --------

    cat data.tsv | tplot -c script.gnu  -e "set output 'output2.png'"
    cat data.tsv | tplot -c script.gnu > ouput3.png

    """
    parser = argparse.ArgumentParser(
        add_help=True,
        description="Plot file from stdin with gnuplot"
    )
    parser.add_argument('-c', '--gnuplot-script', required=True,
                        help="file with gnuplot commangs")
    parser.add_argument('-e', '--gnuplot-commands',
                        help="command1; command2; ...")
    parser.add_argument('--debug', action='store_true', default=False,
                        help="Print result program")

    args = parser.parse_args()
    header = sys.stdin.readline()
    fields = DataDescription.parse(header).fields
    file_name = tempfile.mkstemp()[1]

    # Write data file to temporary location without header.
    # NOTE: gnuplot draw from standard input feature could not be used because
    # file mith be used several times (subplots)
    with open(file_name, 'w') as f:
        for line in sys.stdin:
            f.write(line)

    script_file_name = tempfile.mkstemp()[1]

    substitutors = [
        (index, re.compile("__" + title)) for title, index in sorted([
            (field.title, index) for index, field in enumerate(fields)
        ], reverse=True)
    ]
    with open(script_file_name, 'w') as f:
        with open(args.gnuplot_script) as source:
            for line in source:
                line = re.sub('__input', file_name, line)
                for index, substitutor in substitutors:
                    line = substitutor.sub(str(index + 1), line)

                f.write(line)

    command = 'gnuplot{} -c {}'.format(
        ' -e "{}"'.format(args.gnuplot_commands)
        if args.gnuplot_commands else '',
        script_file_name)

    if args.debug:
        sys.stdout.write("%s\n" % command)
        with open(script_file_name) as f:
            sys.stdout.write(f.read())

    subprocess.call(command, shell=True)
    os.remove(script_file_name)
    os.remove(file_name)
