"""
RPM source file tokenizer
"""

class Special:
    """ Special token """
    def __init__(self, char):
        self.char = char
    def __str__(self):
        return self.char
    def isspace(self):
        "mimic str().isspace()"
        return self.char.isspace()
    def __eq__(self, other):
        if not isinstance(other, Special):
            return False
        return str(other) == self.char
    def __radd__(self, other):
        return str(other) + str(self)
    def __add__(self, other):
        return str(self) + str(other)


def tokenize(string):
    """
    Return either character or special token.
    """
    backslash_mode = False
    for c in string:
        if backslash_mode:
            backslash_mode = False
            if c == "\n":
                yield "follow_line"
            else:
                yield c
        else:
            if c == '\\':
                backslash_mode = True
                continue
            if c in '{}':
                yield Special(c)
                continue
            yield c