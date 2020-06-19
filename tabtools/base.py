""" Base package classes."""
import itertools
from enum import Enum

from .utils import Proxy, ProxyMeta


class Field:

    """Field description."""

    class TYPES(Enum):
        STRING = 'str'
        NUMBER = 'num'


    def __init__(self, title, _type=None):
        if not title:
            raise ValueError("Title should exist")

        if " " in title:
            raise ValueError("field could not have spaces: {}".format(title))

        self.title = title

        if _type is not None:
            try:
                self.type = Field.TYPES(_type)
            except ValueError:
                raise ValueError("Unknown type {}".format(_type))
        else:
            self.type = None

    def __eq__(self, other):
        return isinstance(other, Field) and \
            self.title == other.title and \
            self.type == other.type

    def __str__(self):
        if self.type is None:
            return self.title
        else:
            return "{}:{}".format(self.title, self.type.value)

    def __repr__(self):
        return "<{} ({})>".format(self.__class__.__name__, str(self))

    @classmethod
    def parse(cls, field):
        """ Parse Field from given string.

        :return Field:

        """
        if field.endswith(":"):
            raise ValueError("field does not have a type: {}".format(field))

        return Field(*field.split(":", 1))

    @classmethod
    def union(cls, *fields):
        """Combine multiple headers into one.

        This operation mimics SQL union:
          * if fields have different names, pick the first one.
          * If fields have different types, deduce the result type.

        Args:
          fiels

        Returns:
          Field

        Raises:
          ValueError

        """
        if not fields:
            raise ValueError("At least one field is required")

        types = {f.type for f in fields}

        if None in types:
            _type = None
        elif len(types) == 1:
            _type = list(types)[0]
        elif Field.TYPES.STRING in types:
            _type = Field.TYPES.STRING
        else:
            _type = None

        return Field(fields[0].title, _type)


class Subheader(Proxy, metaclass=ProxyMeta):

    """Subheader of the file."""

    def __init__(self, key, value):
        if not key.isalnum():
            raise ValueError("Key {} is not alphanumeric".format(key))
        self.key = key.lower()
        self.value = value

    def __hash__(self):
        return hash((self.key, self.value))

    def __str__(self):
        return "{}:{}".format(self.key.upper(), self.value)

    def __repr__(self):
        return "<{} ({})>".format(self.__class__.__name__, str(self))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.key == other.key and \
            self.value == other.value

    @classmethod
    def parse(cls, subheader):
        """Parse subheader from a given string.

        :return Subheader:

        """
        key, value = subheader.split(":", 1)
        return cls(key, value)

    @classmethod
    def union(cls, *subheaders):
        """Union subheaders with the same name.

        As far as subheader could consist of any information, it needs to be
        handled manually. By default return a subheader with "?" value.
        ..note: use "?" because it is short and it's value might not matter.
        In concreate class implementation determine what the value should be.

        :param tuple(Subheader): subheader
        :return Subheader:
        :return ValueError:

        """
        if not subheaders:
            raise ValueError("At least one subheader is required")

        subheader_keys = {s.key for s in subheaders}
        if len(subheader_keys) != 1:
            raise ValueError("Subheader keys are not equal {} ".format(
                subheader_keys))

        return Subheader(subheaders[0].key, "?")


class SubheaderCount(Subheader):

    """ Subheader for file size information."""

    def __init__(self, key, value):
        value = int(value)
        super(SubheaderCount, self).__init__(key, value)

    @classmethod
    def union(cls, *subheaders):
        """Union SubheaderCount subheaders.

        :param tuple(SubheaderCount): subheaders
        :return SubheaderCount:
        :return ValueError:

        """
        subheader = Subheader.union(*subheaders).proxy
        subheader.value = sum(x.value for x in subheaders)
        return subheader


class Header:

    """Data description based on the header

    Data header has following format:

    ^(<FIELD>(\t<FIELD>)*)?(<SUBHEADER>)*(<META>)?

    FIELD = ^<str>field_title(:<str>field_type)?$
    SUBHEADER = ^ #<subheader_key>: <subheader_value>$
    SUBHEADER:COUNT, value = size of document

    """

    SUBHEADER_PREFIX = " #"

    def __init__(self, delimiter='\t', fields=None, subheaders=None):
        self.delimiter = delimiter
        self.fields = tuple(fields or ())
        self.subheaders = tuple(subheaders or ())

    def __str__(self):
        return self.delimiter.join(map(str, self.fields)) +\
            "".join([
                self.SUBHEADER_PREFIX + str(subheader)
                for subheader in self.subheaders
            ])

    def __repr__(self):
        return "<{}:\nDelimited: {}\nFields: {}\nSubheaders: {}\n>".format(
            self.__class__.__name__,
            repr(self.delimiter),
            repr(self.fields),
            repr(self.subheaders)
        )

    def __eq__(self, other):
        return isinstance(other, Header) and \
            self.delimiter == other.delimiter and \
            self.fields == other.fields and \
            set(self.subheaders) == set(other.subheaders)

    @staticmethod
    def generate(delimiter, num_columns):
        return Header(
            delimiter=delimiter,
            fields=[Field("f" + str(i)) for i in range(num_columns)]
        )

    @classmethod
    def parse(cls, header, delimiter=None):
        """Parse string into Header object.

        :return DataDescription:

        """
        fields_subheaders = header.rstrip().split(cls.SUBHEADER_PREFIX)


        # If delimit passed, use it. Otherwise consider tabs and commas. Replace tabs with commas and split by comma
        if delimiter is None:
            num_commas = fields_subheaders[0].count(',')
            num_tabs = fields_subheaders[0].count('\t')
            delimiter = '\t' if num_tabs > num_commas else ','

        fields = tuple(
            Field.parse(f)
            for f in fields_subheaders[0].split(delimiter)
        )

        subheaders = [Subheader.parse(s).proxy for s in fields_subheaders[1:]]
        for s in subheaders:
            s.__init__(s.key, s.value)

        return Header(
            delimiter=delimiter, fields=fields, subheaders=subheaders)

    @classmethod
    def union(cls, *headers):
        """Union Headers.

        Fields should be in the same order, number of fields should be equal

        :param tuple(DataDescription): headers
        :return DataDescription:
        :return ValueError:

        """
        fields = tuple(
            Field.union(*fields)
            for fields in zip(*[header.fields for header in headers])
        )

        # Note: Instantiate class to be able to merge
        subheaders = [
            (Subheader(k, "")).proxy.union(*list(key_subheaders))
            for k, key_subheaders in itertools.groupby(
                sorted([
                    subheader
                    for header in headers
                    for subheader in header.subheaders
                ], key=lambda x: x.key),
                lambda x: x.key
            )
        ]

        # Remove headers that could not be explicitly merged
        subheaders = tuple(x for x in subheaders if x.value != "?")
        
        return Header(
            delimiter=headers[0].delimiter,
            fields=fields,
            subheaders=subheaders
        )
