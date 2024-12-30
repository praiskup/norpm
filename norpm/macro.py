"""
RPM macro & macro stack representation
"""

# pylint: disable=too-few-public-methods

class MacroDefinition:
    """A single macro definition."""

    def __init__(self, value, params):
        self.value = value
        self.params = params

    def to_dict(self):
        """Get a serializable object, used for testing."""
        if self.params:
            return (self.value, self.params)
        return (self.value,)


class Macro:
    "stack of MacroDefinition of the same macro"

    def __init__(self):
        self.stack = []

    def define(self, value, parameters=None):
        """Define this macro."""
        self.stack.append(MacroDefinition(value, parameters))

    def to_dict(self):
        """Return the last definition of macro as serializable object."""
        return self.stack[-1].to_dict()


class MacroRegistry:
    """Registry of macro definitions."""

    def __init__(self):
        self.db = {}

    def __getitem__(self, name):
        return self.db[name]

    def __setitem__(self, name, value):
        params = None
        if isinstance(value, tuple):
            value, params = value
        try:
            macro = self.db[name]
        except KeyError:
            macro = self.db[name] = Macro()
        macro.define(value, params)

    def __contains__(self, name):
        return name in self.db

    def to_dict(self):
        """Return a serializable object, used for testing."""
        output = {}
        for name, macrospec in self.db.items():
            output[name] = macrospec.to_dict()
        return output

    @property
    def empty(self):
        """Return True if no macro is defined."""
        return not self.db
