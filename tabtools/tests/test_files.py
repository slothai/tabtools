import unittest

from ..files import File, RegularFile


class TestFile(unittest.TestCase):
    def setUp(self):
        self.fd = open('tabtools/tests/files/sample1.tsv')
        self.f = File(self.fd)

    def test_descriptor(self):
        self.assertTrue(self.f.descriptor.startswith("/dev/fd/"))

    def test_proxy(self):
        self.assertIsInstance(self.f.proxy, RegularFile)
