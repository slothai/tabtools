""" Base package classes."""
from .utils import Choices, Proxy, ProxyMeta
import itertools
from enum import Enum


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


class OrderedField:

    """ Ordered field."""

    SORT_TYPES = Choices(
        ("", "STRING", ""),
        ("M", "MONTH", "month"),
        ("R", "RANDOM", "random"),
        ("V", "VERSION", "version"),
        ("g", "GENERAL_NUMERIC", "general-numeric"),
        ("h", "HUMAN_NUMERIC", "human-numeric"),
        ("n", "NUMERIC", "numeric"),
    )
    SORT_ORDERS = Choices(
        ("", "ASCENDING", "asc"),
        ("r", "DESCENDING", "desc"),
    )
    SORT_TYPES_REVERSED = dict(zip(*reversed(list(zip(*SORT_TYPES)))))
    SORT_ORDERS_REVERSED = dict(zip(*reversed(list(zip(*SORT_ORDERS)))))

    def __init__(self, title, sort_order=None, sort_type=None):
        if " " in title:
            raise ValueError("Field title has space: {}".format(title))

        if sort_type is not None and sort_type not in self.SORT_TYPES:
            raise ValueError("Unknown sort type {}".format(sort_type))

        if sort_order is not None and sort_order not in self.SORT_ORDERS:
            raise ValueError("Unknown sort order {}".format(sort_order))

        self.title = title
        self.sort_type = sort_type or self.SORT_TYPES.STRING
        self.sort_order = sort_order or self.SORT_ORDERS.ASCENDING

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.title == other.title and \
            self.sort_type == other.sort_type and \
            self.sort_order == other.sort_order

    @property
    def sort_flag(self):
        """ Sort flag for unit sort function.

        :return str:

        """
        flag = ""
        if self.sort_type is not None:
            flag += self.sort_type

        if self.sort_order:
            flag += self.sort_order

        return flag

    def __str__(self):
        terms = [self.title, dict(self.SORT_ORDERS)[self.sort_order]]
        if self.sort_type:
            terms.append(dict(self.SORT_TYPES)[self.sort_type])
        return ":".join(terms)

    def __repr__(self):
        return "<{} ({})>".format(self.__class__.__name__, str(self))

    @classmethod
    def parse(cls, ordered_field):
        """ Parse OrderedField from given string.

        :return OrderedField:

        """
        if ordered_field.endswith(":"):
            raise ValueError(
                "OrderedField does not have type: {}".format(ordered_field))

        args = ordered_field.split(":")
        if len(args) > 1:
            if not args[1] in cls.SORT_ORDERS_REVERSED:
                raise ValueError("Sort order {} shoild be in {}".format(
                    args[1], cls.SORT_ORDERS_REVERSED.keys()
                ))

            args[1] = cls.SORT_ORDERS_REVERSED[args[1]]

        if len(args) > 2:
            if not args[2] in cls.SORT_TYPES_REVERSED:
                raise ValueError("Sort type {} shoild be in {}".format(
                    args[2], cls.SORT_TYPES_REVERSED.keys()
                ))

            args[2] = cls.SORT_TYPES_REVERSED[args[2]]

        return OrderedField(*args)


class Subheader(Proxy, metaclass=ProxyMeta):

    """ Subheader of file."""

    def __init__(self, key, value):
        if not key.isalnum():
            raise ValueError("Key {} is not alphanumeric".format(key))
        self.key = key.lower()
        self.value = value

    def __hash__(self):
        return hash((self.key, self.value))

    def __str__(self):
        return "{}: {}".format(self.key.upper(), self.value)

    def __repr__(self):
        return "<{} ({})>".format(self.__class__.__name__, str(self))

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.key == other.key and self.value == other.value

    @classmethod
    def parse(cls, subheader):
        """ Parse subheader from given string.

        :return DataDescriptionSubheader:

        """
        key, value = subheader.split(": ", 1)
        return cls(key, value)

    @classmethod
    def merge(cls, *subheaders):
        """ Merge subheaders with the same name.

        As far as subheader could consist of any information, it needs to be
        handled manually. By default method return subheader with empty value.

        :param tuple(Subheader): subheader
        :return Subheader:
        :return ValueError:

        """
        if not subheaders:
            raise ValueError("At least one subheader is required")

        subheader_keys = {s.key for s in subheaders}
        if len(subheader_keys) != 1:
            raise ValueError("Subheaders keys are not equal {} ".format(
                subheader_keys))

        return DataDescriptionSubheader(subheaders[0].key, "")


class SubheaderOrder(Subheader):

    """ Subheader for fields order information."""

    def __init__(self, key, value):
        super(DataDescriptionSubheaderOrder, self).__init__(key, value)
        self.ordered_fields = [
            OrderedField.parse(f)
            for f in value.split(DataDescription.DELIMITER)
        ]


class SubheaderCount(Subheader):

    """ Subheader for file size information."""

    def __init__(self, key, value):
        value = int(value)
        super(DataDescriptionSubheaderCount, self).__init__(key, value)

    @classmethod
    def merge(cls, *subheaders):
        """ Merge SubheaderCount subheaders.

        :param tuple(DataDescriptionSubheaderCount): subheaders
        :return DataDescriptionSubheaderCount:
        :return ValueError:

        """
        subheader = DataDescriptionSubheader.merge(*subheaders).proxy
        subheader.value = sum(x.value for x in subheaders)
        return subheader


class Header:

    """Data description based on the header

    Data header has following format:

    ^(<FIELD>(\t<FIELD>)*)?(<SUBHEADER>)*(<META>)?

    FIELD = ^<str>field_title(:<str>field_type)?$
    SUBHEADER = ^ #<subheader_key>: <subheader_value>$
    SUBHEADER:COUNT, value = size of document
    SUBHEADER:ORDER, value = <ORDERED_FIELD>( <ORDERED_FIELD>)*
    ORDERED_FIELD = ^<str>field_title(:sort_order)?(:sort_type)?$

    """

    SUBHEADER_PREFIX = " #"

    def __init__(self, delimiter='\t', fields=None, subheaders=None):
        self.delimiter = delimiter
        self.fields = tuple(fields or ())
        self.subheaders = tuple(subheaders or ())

    def __str__(self):
        return self.delimiter.join(map(str, self.fields)) +\
            "".join([
                self.SUBHEADER_PREFIX + subheader
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

    @classmethod
    def parse(cls, header, delimiter=None):
        """Parse string into Header object.

        :return DataDescription:

        """
        fields_subheaders = header.rstrip().split(cls.SUBHEADER_PREFIX)

        fields = tuple(
            Field.parse(f) for f in
            fields_subheaders[0].split(delimiter)
        )

        subheaders = [Subheader.parse(s).proxy for s in fields_subheaders[1:]]
        for s in subheaders:
            s.__init__(s.key, s.value)

        return Header(fields=fields, subheaders=subheaders)

    @classmethod
    def merge(cls, *headers):
        """ Merge Data Descriptions.

        Fields should be in the same order, number of fields should be equal

        :param tuple(DataDescription): headers
        :return DataDescription:
        :return ValueError:

        """
        # self.subheaders = tuple(subheaders or ())
        fields = tuple(
            Field.merge(*fields)
            for fields in zip(header.fields for header in headers)
        )
        key = lambda x: x.key
        # subheaders = [
        #     DataDescriptionSubheader(k, "").proxy.merge(*list(v))
        #     for k, v in itertools.groupby(
        #         sorted((x for dd in dds for x in dd.subheaders), key=key), key
        #     )
        # ]
        # subheaders = tuple(x for x in subheaders if x.value)
        return Header(fields=fields, subheaders=None)
