import argparse


def cat():
    parser = argparse.ArgumentParser(
        add_help=True,
        description="Concatenate files and print on the standard output"
    )
    args = parser.parse_args()
    print(args)
