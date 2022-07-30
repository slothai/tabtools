import unittest
from ..files import File, RegularFile


class TestFile(unittest.TestCase):
    def test_proxy(self):
        with open('tabtools/tests/files/sample1.tsv') as fd:
            f = File(fd, has_header=True)
            self.assertTrue(isinstance(f.proxy, RegularFile))
