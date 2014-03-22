from collections import namedtuple


TYPES = (
    ("str", str),
    ("int", int),
    ("float", float),
    ("null", None),
)

# Sort general-numeric -g, human-numeric -h, month -M, numeric -n, random -R,
# version -V


class Field(namedtuple("Field", ["title", "type"])):
    pass


class DataDescription(object):
    def __init__(self, fields=None, ordering=None, size=None, description=None):
        self.fields = fields or ()
        self.ordering = ordering or ()
        self.size = size
        self.description = description or ""
