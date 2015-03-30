import select
import sys


def has_stdin():
    return bool(select.select([sys.stdin], [], [], 0.0)[0])
