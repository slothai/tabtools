from ..files import File, RegularFile


class TestFile:
    def test_proxy(self):
        with open('tabtools/tests/files/sample1.tsv') as fd:
            f = File(fd, has_header=True)
            assert isinstance(f.proxy, RegularFile)
