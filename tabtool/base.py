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


class OrderedField(Field):
    SORT_TYPES = Choices(
        ("g", "GENERAL_NUMERIC", "general-numeric"),
        ("h", "HUMAN_NUMERIC", "human-numeric"),
        ("M", "MONTH", "month"),
        ("n", "NUMERIC", "numeric"),
        ("R", "RANDOM", "random"),
        ("V", "VERSION", "version"),
    )

    def __init__(self, title, _type=None, sort_type=None, is_reverse=None):
        super(OrderedField, self).__init__(title, _type)
        if sort_type is not None and sort_type not in self.SORT_TYPES:
            raise ValueError("Unknown sort type {}".format(sort_type))

        self.sort_type = sort_type
        self.is_reverse = False if is_reverse is None else bool(is_reverse)


class DataDescription(object):
    def __init__(self, fields=None, ordering=None, size=None, description=None):
        self.fields = fields or ()
        self.ordering = ordering or ()
        self.size = size
        self.description = description or ""
