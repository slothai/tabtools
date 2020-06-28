#!/usr/bin/env python
from setuptools import setup, find_packages
from tabtools import version


with open('README.md', 'r') as f:
    long_description = f.read()


setup(
    name="tabtools",
    version=version,
    packages=find_packages(),

    # metadata for upload to PyPI
    author="Kirill Pavlov",
    author_email="k@p99.io",
    url="https://github.com/slothai/tabtools",
    description="Tools for columnar files manipulation in command line",
    long_description=long_description,
    entry_points={
        "console_scripts": [
            'ttsort = tabtools.scripts:ttsort',
            'ttmap = tabtools.scripts:ttmap',
            'ttreduce = tabtools.scripts:ttreduce',
            'ttplot = tabtools.scripts:ttplot',
        ]
    },
    scripts=[
        "bin/tttail",
        "bin/ttpretty",
    ],
    # Full list:
    # https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.4",
    license="MIT",
)
