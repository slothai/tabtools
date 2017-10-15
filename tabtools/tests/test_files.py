import unittest
import sys

try:
    from unittest.mock import patch
    from io import StringIO
except ImportError:
    from mock import patch
    from StringIO import StringIO

from ..files import File, StreamFile, RegularFile


class TestFile(unittest.TestCase):
    def setUp(self):
        self.fd = open('tabtools/tests/files/sample1.tsv')
        self.f = File(self.fd)

    def test_proxy(self):
        self.assertIsInstance(self.f.proxy, RegularFile)
