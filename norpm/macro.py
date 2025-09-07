"""
RPM macro & macro stack representation
"""

# pylint: disable=too-few-public-methods
from norpm.arch import detect_host_arch

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

    @property
    def params(self):
        """True if the latest definition is parametric."""
        return self.stack[-1].params


class MacroRegistry:
    """Registry of macro definitions."""

    def __init__(self):
        self.db = {}
        self.target = detect_host_arch()

    def known_norpm_hacks(self):
        """
        Define some value for %optflags and similar.
        """
        # The %optflags are defined using rpmrc, and some packages do things
        # like '%global optflags --foo %optflags' leading to recursion error.
        self["optflags"] = "-O2 -g3"
        # The %goname method is typically defined by %gometa, which is a
        # complicated lua script that we don't interpret.
        self["goname"] = "NORPM_HACK_NO_GONAME"
        self["verbose"] = "0"

    def __getitem__(self, name):
        return self.db[name]

    def __setitem__(self, name, value):
        self.define(name, value)

    def define(self, name, value, special=False):
        """(re)define macro"""
        params = None

        if not special and not is_macro_name(name):
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

    def undefine(self, name):
        """Undefine macro in registry"""
        if name not in self.db:
            return

        macro = self.db[name]
        macro.stack.pop()
        if macro.stack:
            return

        del self.db[name]

    def clear(self, name):
        """
        Remove the macro from database, not just "pop once".
        """
        while name in self.db:
            self.undefine(name)


    @property
    def empty(self):
        """Return True if no macro is defined."""
        return not self.db

    def get_macro_value(self, name, fallback):
        """Return the macro definition string, or return fallback if not
        defined.
        """
        try:
            definition = self[name].value
            return definition
        except KeyError:
            if name.startswith("-"):
                return ""
            return fallback


def is_macro_character(c):
    """Return true if character c can be part of macro name"""
    if c.isalnum():
        return True
    if c in ["-", "_", "*", "#"]:
        return True
    return False


def is_macro_name(name):
    """
    Return True if Name is a valid RPM macro name
    """
    if name == '#':
        return True
    if not name[0].isalpha() and name[0] != '_':
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

    # pylint: disable=too-many-branches
    success = True

    if call.startswith("%{"):
        call = call[2:-1]
    else:
        call = call[1:]

    conditionals = set()
    name = ""
    params = None
    alt = None
    single_param = False

    state = 'COND'
    for c in call:
        if state == 'COND':
            if c in '?':
                conditionals.add(c)
                continue
            if c in '!':
                conditionals ^= set(c)
                continue
            if c.isspace():
                success = False
                break
            if is_macro_character(c):
                name += c
                state = 'NAME'
                continue
            if c == '#':
                name += c
                continue
            success = False
            break

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
                single_param = True
                continue

            if c.isspace():
                state = 'PARAMS'
                params = ""
                continue

            success = False
            break

        if state == 'PARAMS':
            params += c
            continue

        if state == 'ALT':
            alt += c
            continue

    if not name:
        success = False

    # Handle '%{foo:single_param}' vs '%{foo multi param}', this mapping is
    # later handled by _expand_params().
    if not single_param:
        if params is None:
            params = []
        else:
            params = [params]

    return success, name, conditionals, params, alt
