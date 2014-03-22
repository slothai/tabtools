from .utils import Choices


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
        if " " in title:
            raise ValueError("Field title has space: {}".format(title))

        if _type is not None and _type not in self.TYPES:
            raise ValueError("Unknown type {}".format(_type))

        self.title = title
        self.type = _type or self.TYPES.NULL

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.title == other.title and self.type == other.type

    def __repr__(self):
        return "<{} ({}:{})>" % (
            self.__class__.__name__, self.title, self.type
        )

    def __str__(self):
        if self.type == self.TYPES.NULL:
            return self.title
        else:
            return "{}:{}".format(self.title, self.type)

    @classmethod
    def parse(cls, field):
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

    @classmethod
    def parse(cls, ordered_field):
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


class DataDescriptionSubheader(object):

    """ Subheader of file."""

    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __str__(self):
        return " #{}: {}".format(self.key, self.value)

    def __eq__(self, other):
        return isinstance(other, self.__class__) and \
            self.key == other.key and self.value == other.value

    @classmethod
    def parse(cls, subheader):
        prefix = " #"
        if not subheader.startswith(prefix):
            raise ValueError("Subheader should start with '{}'".format(prefix))
        key, value = subheader[len(prefix):].split(": ", 1)
        return cls(key, value)


class DataDescriptionSubheaderOrder(DataDescriptionSubheader):
    def __init__(self, key, value):
        super(DataDescriptionSubheaderOrder, self).__init__(key, value)
        self.ordered_fields = [
            f for f in value.split(DataDescription.DELIMITER)
        ]


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

    def __init__(self, fields=None, subheaders=None, meta=None):
        self.fields = fields or ()
        self.subheaders = subheaders or {}
        self.meta = meta

    def __str__(self):
        return "# {}{}".format(
            self.DELIMITER.join(map(str, self.fields)),
            "".join(map(str, list(self.subheaders) + [self.meta]))
        )
