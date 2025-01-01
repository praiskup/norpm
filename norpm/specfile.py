"""
Spec file parser
"""

from collections import deque

from norpm.tokenize import tokenize, Special
from norpm.macro import is_macro_name

# pylint: disable=too-many-statements,too-many-branches


def parse_specfile(file_contents, _macros):
    """
    Parse file_contents string into a list of parts, macros and raw string
    snippets.
    """
    return [i for i in get_parts(file_contents, _macros) if i != ""]


def is_special(name):
    """Return True if the macro name is a special construct"""
    special = {"if", "else", "endif", "setup"}
    return name in special


def is_definition(name):
    """Return True if the Name is a macro definition keyword"""
    special = {"define", "global"}
    return name in special


def get_parts(string, macros):
    """
    Split input string into a macro and non-macro parts.
    """
    state = "TEXT"
    depth = 0

    buffer = ""
    for c in tokenize(string):
        if state == "TEXT":
            if c != "%":
                buffer += c
                continue

            yield buffer
            buffer = c
            state = "MACRO_START"
            continue

        if state == "MACRO_START":
            if c == Special("{"):
                buffer += c
                state = "MACRO_CURLY"
                continue

            if c.isspace():
                yield buffer
                state = "TEXT"
                buffer = c
                continue

            if c == "%":
                buffer += "%"
                yield buffer
                buffer = ""
                state = "TEXT"
                continue

            if c.isalnum():
                buffer += c
                state = "MACRO"
                continue

            yield buffer
            state = "TEXT"
            buffer = c
            continue

        if state == "MACRO":
            if c.isalnum():
                buffer += c
                continue

            if c == "%":
                yield buffer
                buffer = "%"
                state = "MACRO_START"
                continue

            if c == ' ':
                macroname = buffer[1:]
                if is_special(macroname) or \
                        macroname in macros and macros[macroname].parametric:
                    state = "MACRO_PARAMETRIC"
                    buffer += c
                    continue

                if is_definition(macroname):
                    state = "MACRO_DEFINITION"
                    buffer += c
                    continue

            yield buffer
            state = "TEXT"
            buffer = c
            continue

        if state == "MACRO_CURLY":
            if c == Special('{'):
                depth += 1
                buffer += c
                continue

            if depth:
                if c == Special('}'):
                    depth -= 1
                    buffer += c
                else:
                    buffer += c
                continue

            if c == Special('}'):
                buffer += c
                yield buffer
                buffer = ""
                state = "TEXT"
                continue

            buffer += c
            continue

        if state == "MACRO_PARAMETRIC":
            if c == Special('\n'):
                yield buffer
                buffer = ""
                state = "TEXT"
                continue
            if c == "\n":
                yield buffer
                buffer = "\n"
                state = "TEXT"
                continue

            buffer += c
            continue

        if state == "MACRO_DEFINITION":
            if c == Special("\n"):
                buffer += "\\\n"
                continue

            if c == Special('{'):
                depth += 1
                buffer += c
                continue

            if depth:
                if c == Special('}'):
                    depth -= 1
                    buffer += c
                else:
                    buffer += c
                continue

            if c == "\n":
                yield buffer
                buffer = "\n"
                state = "TEXT"
                continue

            buffer += c
            continue

    yield buffer


def expand_macro(macroname, definitions, fallback):
    if macroname not in definitions:
        return fallback
    return definitions[macroname].value()


def _expand_snippet(snippet, definitions):
    if snippet in ['%', '%%']:
        return '%'
    if not snippet.startswith("%"):
        return snippet

    if snippet.startswith("%{"):
        if is_macro_name(snippet[2:-1]):
            return expand_macro(snippet[2:-1], definitions, snippet)
        return "TODO"

    if is_macro_name(snippet[1:]):
        return expand_macro(snippet[1:], definitions, snippet)

    return "TODO"


def expand_macros(snippets, definitions):
    "expand macros in parse_specfile() output"

    return [_expand_snippet(s, definitions) for s in snippets]


def expand_string(string, macros):
    """ expand macros in string """
    parts = list(get_parts(string, macros))
    todo = deque(parts)
    while todo:
        string = todo.popleft()
        if not string.startswith('%'):
            yield string
            continue
        expanded = _expand_snippet(string, macros)
        if expanded == string:
            yield string
            continue
        add = [x for x in  list(get_parts(expanded, macros)) if x != ""]
        add.reverse()
        todo.extendleft(add)
