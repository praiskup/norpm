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

    @property
    def defined(self):
        """Return True if the macro is defined."""
        return bool(self.stack)

    def to_dict(self):
        """Return the last definition of macro as serializable object."""
        return self.stack[-1].to_dict()


class MacroRegistry:
    """Registry of macro definitions."""

    def __init__(self):
        self.db = {}

    def __getitem__(self, name):
        if name not in self.db:
            self.db[name] = Macro()
        return self.db[name]

    def to_dict(self):
        """Return a serializable object, used for testing."""
        output = {}
        for name, macrospec in self.db.items():
            if macrospec.defined:
                output[name] = macrospec.to_dict()
        return output

    def empty(self):
        """Return True if no macro is defined."""
        return not any(x.defined() for x in self.db)
