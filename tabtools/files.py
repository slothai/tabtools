"""File list abstraction module."""
import os
import subprocess
import sys

from .base import Header
from .utils import cached_property


class File:

    """File base class.

    Attributes:
    fd - file descriptor
    has_header (bool=True) whether file has header or not.

    """

    def __init__(self, fd, has_header):
        """ Init fie object.

        :param fd: file descriptor
        file = File(fd).proxy

        """
        self.fd = fd
        self.has_header = has_header

    @property
    def header(self):
        if self.header_line is None:
            raise ValueError("Header line is not defined")
        return Header.parse(self.header_line)

    def generate_header(self):
        """Generate header based on the data line.

        As delimiter and and number of columns are not known, parse the first
        data line as if it is header and determine unknown parameters.

        Return: Header
        """
        header = Header.parse(self.first_data_line)
        return Header.generate(header.delimiter, len(header.fields))

    @property
    def proxy(self):
        """ Return file with actual type."""
        try:
            self.fd.tell()
        except IOError:
            return StreamFile(self.fd, self.has_header)
        except ValueError:
            # Operation on closed descriptor
            return None
        else:
            return RegularFile(self.fd, self.has_header)


class RegularFile(File):

    """ Regular file according to file types.

    http://en.wikipedia.org/wiki/Unix_file_types

    """

    def __init__(self, fd, has_header):
        super(RegularFile, self).__init__(fd, has_header)

        if has_header:
            self.header_line = self.readline()
        else:
            self.first_data_line = self.readline()

    def readline(self):
        """ Return regular file header."""
        with open(self.fd.name) as f:
            line = f.readline()
        return line

    @property
    def body_descriptor(self):
        """ Return regular file descriptor.

        Regular file has header, descriptor consists of lines starting
        from second.

        """
        os.lseek(self.fd.fileno(), 0, os.SEEK_SET)
        if self.has_header:
            return "<(tail -qn+2 {})".format(self.fd.name)
        else:
            return self.fd.name


class StreamFile(File):

    """ General input stream.

    .. note: StreamFile could be read only once, seek is not allowed.

    """

    def __init__(self, fd, has_header):
        super(StreamFile, self).__init__(fd, has_header)

        if has_header:
            self.header_line = self.readline()
        else:
            self.first_data_line = self.readline()

    def readline(self):
        """Read one line and return it."""
        chars = []
        while True:
            char = os.read(self.fd.fileno(), 1).decode('utf8')
            if char is None or char == '' or char == '\n':
                break
            chars.append(char)

        if chars:
            return ''.join(chars)
        else:
            return None

    @property
    def body_descriptor(self):
        """ Return file descriptor in system."""
        # NOTE: it is important to combine two file descriptors into one.
        # Otherwise commands like tail would treat both stream independently and
        # produce incorrect result (e.g. extra line for tail).
        # This looks not great as one need to combile a line (echo-ed) with the
        # rest of the stream into one stream.
        # https://unix.stackexchange.com/questions/64736/
        #   combine-output-from-two-commands-in-bash
        if self.has_header:
            return '/dev/fd/' + str(self.fd.fileno())
        else:
            return "<(cat <(echo \"{}\") <(cat /dev/fd/{}))".format(
                self.first_data_line, self.fd.fileno())


class FileList(list):

    """A List of Files.

    header_line =
        None - generate header, files do not have headers.
        '' - get from files, assume each file has a header
        <str> - use passed header, files should not have headers
    header should be an instance of a Header class.

    """

    def __init__(self, files=None, header_line=''):
        files = files or [sys.stdin]
        has_header = (header_line == '')
        super(FileList, self).__init__([File(f, has_header).proxy for f in files])
        self.header_line = header_line

    @property
    def body_descriptors(self):
        """ Return list of file descriptors."""
        return [f.body_descriptor for f in self]

    @property
    def header(self):
        """ Get header for files list.

        :return str: header
        :raise ValueError:

        """
        if self.header_line is None:
            # generate header
            return Header.union(*[
                f.generate_header() for f in self
            ])

        if self.header_line == '':
            # use header from files
            return Header.union(*[
                f.header for f in self
            ])

        # use provided header
        return Header.parse(self.header_line)

    def __call__(self, *args, **kwargs):
        command = [
            '/bin/bash', '-o', 'pipefail', '-o', 'errexit', '-c',
        ]
        args = list(args)
        subcommand = " ".join(
            ['LC_ALL=C', args.pop(0)] + args + self.body_descriptors
        )
        command.append(subcommand)
        subprocess.call(command)
