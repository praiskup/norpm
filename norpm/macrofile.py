"""
Parse macro file into a "macroname = unexpanded value" dictionary
"""

import glob
from dataclasses import dataclass
import os

from norpm.macro import MacroRegistry
from norpm.tokenize import tokenize, Special, BRACKET_TYPES, OPENING_BRACKETS
from norpm.logging import get_logger

log = get_logger()

@dataclass
class _CTX():
    def __init__(self):
        self.state = "START"
        self.macroname = ""
        self.params = ""
        self.value = ""


def macrofile_parse(file_contents, macros, inspec=False):
    """Parse macro file (in a string format, containing '%foo bar' macro
    definitions), and store the definitions to macros registry.  See
    macrofile_split_generator() what inspec=True means.
    """
    for name, value, params in macrofile_split_generator(file_contents, inspec):
        macros[name] = (value, params)


def macrofile_split_generator(file_contents, inspec=False):
    """Generator method.  Yield (macroname, value, params) n-aries from macro
    file definition file_contents.  If inspec=True is defined, the `%define` and
    `%global` statements are parsed (leads to a different EOL interpretation).
    """
    # pylint: disable=too-many-branches,too-many-statements

    ctx = _CTX()
    ctx.state = "START"
    ctx.macroname = ""
    ctx.value = ""
    ctx.params = None
    depth = 0
    brackets = None

    def _reset():
        ctx.state = "START"
        ctx.macroname = ""
        ctx.value = ""
        ctx.params = None

    for c in tokenize(file_contents):
        if ctx.state == "START":
            if c.isspace():
                continue
            if c == '%':
                ctx.state = "MACRO_START"
                continue
            ctx.state = "IGNORE_TIL_EOL"
            continue

        if ctx.state == "MACRO_START":
            if c.isspace():
                continue
            ctx.macroname += c
            ctx.state = "MACRO_NAME"
            continue

        if ctx.state == "MACRO_NAME":
            if c == Special("\n"):
                ctx.state = "VALUE"
                ctx.value += "\n"
                continue

            if c.isspace():
                log.debug("macro name: %s", ctx.macroname)
                ctx.state = "VALUE_START"
                continue

            if c == Special('('):
                ctx.state = 'PARAMS'
                ctx.params = ""
                continue

            ctx.macroname += c
            continue

        if ctx.state == 'PARAMS':
            if c == Special(')'):
                ctx.state = "VALUE_START"
                continue
            ctx.params = ctx.params + c
            continue

        if ctx.state == "VALUE_START":
            if inspec and c == "\n":
                ctx.value += "\n"
                ctx.state = "VALUE"
                continue

            if c == Special("\n"):
                if not inspec:
                    ctx.value += "\n"
                    ctx.state = "VALUE"
                continue
            if c.isspace():
                continue
            ctx.value += c
            ctx.state = "VALUE"
            continue

        if ctx.state == "VALUE":
            if c == Special("\n"):
                if not inspec:
                    ctx.value += "\n"
                continue

            if depth == 0 and c in OPENING_BRACKETS:
                brackets = BRACKET_TYPES[str(c)]
                depth += 1
                ctx.value += c
                continue

            if depth and c == brackets[0]:
                depth += 1
                ctx.value += c
                continue

            if depth:
                if c == brackets[1]:
                    depth -= 1
                    ctx.value += c
                else:
                    ctx.value += c
                continue
            if c == '\n' and not inspec:
                yield ctx.macroname, ctx.value.rstrip(), ctx.params
                _reset()
                continue

            ctx.value += c
            continue

        if ctx.state == "IGNORE_TIL_EOL":
            if c == '\n':
                _reset()
            continue

    if ctx.state == "VALUE":
        yield ctx.macroname, ctx.value.rstrip(), ctx.params

    if ctx.state == "VALUE_START" and inspec:
        yield ctx.macroname, ctx.value.rstrip(), ctx.params


def _get_macro_files(arch):
    patterns = [
        "/usr/lib/rpm/macros",
        "/usr/lib/rpm/redhat/macros",
        f"/usr/lib/rpm/platform/{arch}-linux/macros",
        "/usr/lib/rpm/macros.d/macros.*",
        os.path.join(os.path.expanduser("~"), ".rpmmacros"),
    ]
    files = []
    for pattern in patterns:
        for file in glob.glob(pattern):
            files.append(file)
    return files


def system_macro_registry(arch=None):
    """Create and return a new MacroRegistry() object fed with the macros
    defined on the system."""
    registry = MacroRegistry()

    if arch:
        registry.target = arch

    for file in _get_macro_files(arch):
        with open(file, "r", encoding="utf-8") as fd:
            macrofile_parse(fd.read(), registry)
    return registry
