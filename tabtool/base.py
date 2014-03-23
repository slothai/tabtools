""" Base package classes."""
from drugs.enum import Choices
from drugs.mixins import Proxy, ProxyMeta
from . import six


class Field(object):

    """ Field description."""

    TYPES = Choices(
        ("str", "STR"),
        ("int", "INT"),
        ("float", "FLOAT"),
        ("bool", "BOOL"),
        ("null", "NULL"),
    )

    def __init__(self, title, _type=None):
        if not title:
            raise ValueError("Title should exist")

        if " " in title:
            raise ValueError("Field title has space: {}".format(title))

        if _type is not None and _type not in self.TYPES:
            raise ValueError("Unknown type {}".format(_type))

        self.title = title
        self.type = _type or self.TYPES.NULL

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.title == other.title and self.type == other.type

    def __str__(self):
        if self.type == self.TYPES.NULL:
            return self.title
        else:
            return "{}:{}".format(self.title, self.type)

    def __repr__(self):
        return "<{} ({})>".format(self.__class__.__name__, str(self))

    @classmethod
    def parse(cls, field):
        """ Parse Field from given string.

        :return Field:

        """
        if field.endswith(":"):
            raise ValueError("field does not have type: {}".format(field))

        return Field(*field.split(":"))


class OrderedField(object):

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


@six.add_metaclass(ProxyMeta)
class DataDescriptionSubheader(Proxy):

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


class DataDescriptionSubheaderOrder(DataDescriptionSubheader):

    """ Subheader for fields order information."""

    def __init__(self, key, value):
        super(DataDescriptionSubheaderOrder, self).__init__(key, value)
        self.ordered_fields = [
            OrderedField.parse(f)
            for f in value.split(DataDescription.DELIMITER)
        ]


class DataDescriptionSubheaderSize(DataDescriptionSubheader):

    """ Subheader for file size information."""

    def __init__(self, key, value):
        value = int(value)
        super(DataDescriptionSubheaderSize, self).__init__(key, value)


class DataDescription(object):

    """ Data description, taken from header.

    Data header has following format:

    ^# (<FIELD>( <FIELD>)*)?(<SUBHEADER>)*(<META>)?

    FIELD = ^<str>field_title(:<str>field_type)?$
    SUBHEADER = ^ #<subheader_key>: <subheader_value>$
    SUBHEADER:SIZE, value = size of document
    SUBHEADER:ORDER, value = <ORDERED_FIELD>( <ORDERED_FIELD>)*
    ORDERED_FIELD = ^<str>field_title(:sort_order)?(:sort_type)?$
    META = ^( )*#META: [^n]*

    """

    DELIMITER = " "
    PREFIX = "# "
    SUBHEADER_PREFIX = " #"

    def __init__(self, fields=None, subheaders=None, meta=None):
        self.fields = tuple(fields or ())
        self.subheaders = tuple(subheaders or ())
        self.meta = meta

    def __str__(self):
        subheaders = list(self.subheaders)
        if self.meta is not None:
            subheaders.append(self.meta)

        return self.PREFIX + "".join(
            [self.DELIMITER.join(map(str, self.fields))] +
            list(map(lambda s: self.SUBHEADER_PREFIX + str(s), subheaders))
        )

    def __repr__(self):
        return "<{}:\nFields: {}\nSubheaders: {}\nMeta: {}\n>".format(
            self.__class__.__name__,
            repr(self.fields),
            repr(self.subheaders),
            repr(self.meta)
        )

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.fields == other.fields and \
            set(self.subheaders) == set(other.subheaders) and \
            self.meta == other.meta

    @classmethod
    def parse(cls, header):
        """ Parse string into DataDescription object.

        :return DataDescription:

        """
        if not header.startswith(cls.PREFIX):
            raise ValueError(
                "Header {} should start with {}".format(header, cls.PREFIX))

        fields_subheaders_and_meta = header[len(cls.PREFIX):].split(
            "#META: ", 1)
        fields_subheaders = fields_subheaders_and_meta[0]
        meta = None if len(fields_subheaders_and_meta) == 1 else \
            DataDescriptionSubheader("META", fields_subheaders_and_meta[1])

        fields_and_subheaders = fields_subheaders.rstrip().split(
            cls.SUBHEADER_PREFIX)

        fields = tuple(
            Field.parse(f) for f in
            fields_and_subheaders[0].split(cls.DELIMITER) if f
        )

        subheaders = [
            DataDescriptionSubheader.parse(s).proxy
            for s in fields_and_subheaders[1:]
        ]
        for s in subheaders:
            s.__init__(s.key, s.value)

        fields_set = {f.title for f in fields}
        ordered_fields_set = {
            f.title for s in subheaders
            if isinstance(s, DataDescriptionSubheaderOrder)
            for f in s.ordered_fields
        }
        if not ordered_fields_set <= fields_set:
            raise ValueError(
                "Ordered fields {} should be subset of fields {}".format(
                    ordered_fields_set, fields_set))

        return DataDescription(fields=fields, subheaders=subheaders, meta=meta)
