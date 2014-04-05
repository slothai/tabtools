""" Files and streams utility."""
import os
import subprocess
from .base import DataDescription


class File(object):

    """ File base class."""

    def __init__(self, fd):
        """ Init fie object.

        :param fd: file descriptor
        file = File(fd).proxy

        """
        self.fd = fd

    @property
    def descriptor(self):
        """ Return file descriptor in system."""
        return "/dev/fd/{}".format(self.fd.fileno())

    @property
    def proxy(self):
        """ Return file with actual type."""
        try:
            self.fd.tell()
        except IOError:
            return StreamFile(self.fd)
        except ValueError:
            # Operation on closed descriptor
            return None
        else:
            return RegularFile(self.fd)


class StreamFile(File):

    """ General input stream."""

    @property
    def header(self):
        """ Return stream file header."""
        header = ""
        while True:
            char = os.read(self.fd.fileno(), 1)
            if char is None or char == '\n':
                break
            header += char
        return header


class StdinFile(StreamFile):

    """ Stdin input stream."""

    pass


class RegularFile(File):

    """ Regular file according to file types.

    http://en.wikipedia.org/wiki/Unix_file_types

    """

    @property
    def header(self):
        """ Return regular file header."""
        with open(self.fd.name) as f:
            header = f.readline()
        return header

    @property
    def descriptor(self):
        """ Return regular file descriptor."""
        os.lseek(self.fd.fileno(), 0, os.SEEK_SET)
        return "<(tail -qn+2 {} || kill $$)".format(
            super(RegularFile, self).descriptor)


class FileList(list):

    """ List of Files."""

    def __init__(self, files=None):
        files = map(lambda f: File(f).proxy, files or [])
        super(FileList, self).__init__(files)

    @property
    def descriptors(self):
        """ Return list of file descriptors."""
        return [f.descriptor for f in self]

    @property
    def description(self):
        """ Get data description.

        :return DataDescription:

        """
        return DataDescription.merge(
            *[DataDescription.parse(f.header) for f in self])

    @property
    def header(self):
        """ Get header for files list.

        :return str: header
        :raise ValueError:

        """
        return str(self.description)

    def __call__(self, *args, **params):
        command = [
            'bash', '-o', 'pipefail', '-o', 'errexit', '-c',
        ]
        subcommand = " ".join(['LC_ALL=C'] + list(args) + self.descriptors)
        command.append(subcommand)
        if params.get("is_debug"):
            print(" ".join(command))
        print(self.header)
        subprocess.call(command)
