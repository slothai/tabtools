""" Files and streams utility."""
import os
import sys
import subprocess
from .base import DataDescription
from .utils import cached_property


class File(object):

    """ File base class."""

    def __init__(self, fd):
        """ Init fie object.

        :param fd: file descriptor
        file = File(fd).proxy

        """
        self.fd = fd

    def readline(self):
        raise NotImplementedError("Implement this method in derided class")

    @property
    def has_header(self):
        if self._first_line is None:
            return False

        try:
            DataDescription.parse(self._first_line)
            return True
        except ValueError:
            return False

    @property
    def header(self):
        if not self.has_header:
            raise ValueError("File {} does not have header.".format(self.fd))
        return self._first_line

    @property
    def autoheader(self):
        return DataDescription.generate_header(self._first_data_line)

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

    """ General input stream.

    .. note: StreamFile could be read only once, seek is not allowed.

    """
    def __init__(self, fd):
        super(StreamFile, self).__init__(fd)
        self._first_line = self.readline()
        self._first_data_line = self.readline() if self.has_header \
            else self._first_line

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
        descriptor = "<(cat <(echo \"{}\") <(cat /dev/fd/{}))".format(
            self._first_data_line, self.fd.fileno())
        return descriptor


class RegularFile(File):

    """ Regular file according to file types.

    http://en.wikipedia.org/wiki/Unix_file_types

    """
    def __init__(self, fd):
        super(RegularFile, self).__init__(fd)
        self._first_line = self.readline()
        self._first_data_line = self.readline() if self.has_header \
            else self._first_line

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
            return "<( tail -qn+2 {} )".format(self.fd)
        else:
            return self.fd


class FileList(list):

    """ List of Files."""

    def __init__(self, files=None, header=None, should_generate_header=None):
        files = files or [sys.stdin]
        super(FileList, self).__init__([File(f).proxy for f in files])
        self._header = header
        self.should_generate_header = should_generate_header or False

    @property
    def body_descriptors(self):
        """ Return list of file descriptors."""
        return [f.body_descriptor for f in self]

    @cached_property
    def description(self):
        """ Get data description.

        .. note: cache property to allow multiple header access in case of
        stream files.

        Return
        ------
        DataDescription

        """
        if self._header:
            return DataDescription.parse(self._header)
        else:
            headers = [
                f.autoheader if self.should_generate_header else f.header
                for f in self
            ]
            return DataDescription.merge(*[
                DataDescription.parse(header) for header in headers
            ])

    @property
    def header(self):
        """ Get header for files list.

        :return str: header
        :raise ValueError:

        """
        return str(self.description)

    def __call__(self, *args, **kwargs):
        command = [
            'bash', '-o', 'pipefail', '-o', 'errexit', '-c',
        ]
        args = list(args)
        subcommand = " ".join(
            ['LC_ALL=C', args.pop(0)] + args + self.body_descriptors
        )
        command.append(subcommand)
        subprocess.call(command)
