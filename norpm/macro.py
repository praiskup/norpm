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

    @property
    def value(self):
        """Value of the last macro definition."""
        return self.stack[-1].value

    @property
    def parametric(self):
        """True if the latest definition is parametric."""
        return self.stack[-1].params is not None


class MacroRegistry:
    """Registry of macro definitions."""

    def __init__(self):
        self.db = {}

    def rpmrc_hack(self):
        """
        Define some value for optflags and similar.
        """
        self["optflags"] = "-O2 -g3"

    def __getitem__(self, name):
        return self.db[name]

    def __setitem__(self, name, value):
        params = None

        if not is_macro_name(name):
            raise KeyError(f"{name} is not a valid macro name")

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


def is_macro_character(c):
    """Return true if character c can be part of macro name"""
    if c.isalnum():
        return True
    if c == '_':
        return True
    return False


def is_macro_name(name):
    """
    Return True if Name is a valid RPM macro name
    """
    if not name[0].isalpha() and name[0] != '_':
        return False
    if len(name) < 3:
        return False
    return all(is_macro_character(c) for c in name)


def parse_macro_call(call):
    """Given a macro call, return 4-ary
        (success, name, conditionals, params)
    Where SUCCESS is True/False, depending if the parsing was done correctly.
    NAME is the macro name being called.
    CONDITIONALS is a set of '?' or '!' characters.
    PARAMS are optional parameters
    ALT is alternative text after colon
    """


    # %macro
    # %?macro
    # %!?macro # empty
    # %{macro}
    # %{?macro}  %{?macro:foo}  # different for parametrized
    # %{!?macro} %{!?macro:foo}
    # %{macro args}
    # %{?macro args}

    success = True

    if call.startswith("%{"):
        call = call[2:-1]

    conditionals = set()
    name = ""
    params = None
    alt = None

    state = 'COND'
    for c in call:
        if state == 'COND':
            if c in '?!':
                conditionals.add(c)
                continue
            if c.isspace():
                success = False
                break
            if is_macro_character(c):
                name += c
                state = 'NAME'
                continue
        if state == 'NAME':
            if is_macro_character(c):
                name += c
                continue

            if c == ':':
                if '?' in conditionals:
                    state = 'ALT'
                    alt = ""
                    continue
                params = ""
                state = 'PARAMS'
                continue

            if c.isspace():
                state = 'PARAMS'
                params = ""
                continue

        if state == 'PARAMS':
            params += c
            continue

        if state == 'ALT':
            alt += c
            continue

    return success, name, conditionals, params, alt
