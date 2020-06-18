from ..files import File, RegularFile


class TestFile:
    def test_proxy(self):
        with open('tabtools/tests/files/sample1.tsv') as fd:
            f = File(fd)
            assert isinstance(f.proxy, RegularFile)
