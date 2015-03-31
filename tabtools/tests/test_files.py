import unittest

from ..files import File


class TestFile(unittest.TestCase):
    def setUp(self):
        self.f = File(open('tabtools/tests/files/sample1.tsv'))

    def test_descriptor(self):
        self.assertTrue(self.f.descriptor.startswith("/dev/fd/3"))

    def test_proxy(self):
        pass