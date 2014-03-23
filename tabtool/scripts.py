""" Scripts of tool."""
import argparse


def cat():
    """ cat function."""
    parser = argparse.ArgumentParser(
        add_help=True,
        description="Concatenate files and print on the standard output"
    )
    args = parser.parse_args()
    print(args)
