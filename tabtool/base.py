from .utils import Choices


class Field(object):

    """ Field description."""

    TYPES = Choices(
        ("str", "STR"),
        ("int", "INT"),
        ("float", "FLOAT"),
        ("null", "NULL"),
    )

    def __init__(self, title, _type=None):
        if _type is not None and _type not in self.TYPES:
            raise ValueError("Unknown type {}".format(_type))

        self.title = title
        self.type = _type or self.TYPES.NULL

    def __repr__(self):
        return "<{} ({}:{})>" % (
            self.__class__.__name__, self.title, self.type
        )

    def __str__(self):
        if self.type == self.TYPES.NULL:
            return self.title
        else:
            return "{}:{}".format(self.title, self.type)


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

    def __init__(self, title, sort_type=None, sort_order=None):
        if sort_type is not None and sort_type not in self.SORT_TYPES:
            raise ValueError("Unknown sort type {}".format(sort_type))

        if sort_order is not None and sort_order not in self.SORT_ORDERS:
            raise ValueError("Unknown sort order {}".format(sort_order))

        self.title = title
        self.sort_type = sort_type or self.SORT_TYPES.STRING
        self.sort_order = sort_order or self.SORT_ORDERS.ASCENDING

    @property
    def sort_flag(self):
        flag = ""
        if self.sort_type is not None:
            flag += self.sort_type

        if self.sort_order:
            flag += self.sort_order

        return flag

    def __str__(self):
        return ":".join([self.title, self.sort_order])


class DataDescription(object):

    """ Data description, taken from header.

    Data header has following format:

        ^# (<FIELD>( <FIELD>)*)?(<SUBHEADER>)*(<META>)?

        FIELD = ^<str>field_title(:<str>field_type)?$
        SUBHEADER = ^ #<subheader_key>: <subheader_value>$
        SUBHEADER:SIZE, value = size of document
        SUBHEADER:ORDER, value = <ORDERED_FIELD>( <ORDERED_FIELD>)*
        ORDERED_FIELD = ^<str>field_title(:sort_order)?(:sort_type)?$
        META = ^ #META: [^\n]*

    """

    DELIMITERS = (",", " ", "\t")
    DELIMITER = " "

    def __init__(self, fields=None, ordering=None, size=None, description=None):
        self.fields = fields or ()
        self.ordering = ordering or ()
        self.size = size
        self.description = description or ""
