"""
Spec file parser
"""

from collections import deque

from norpm.tokenize import tokenize, Special
from norpm.macro import is_macro_name, is_macro_character
from norpm.macrofile import parse_rpmmacros

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

            if is_macro_character(c):
                buffer += c
                state = "MACRO"
                continue

            yield buffer
            state = "TEXT"
            buffer = c
            continue

        if state == "MACRO":
            if is_macro_character(c):
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
                # We intentionally eat the newline, and not add this
                # to the buffer. That's what RPM does.
                buffer = ""
                state = "TEXT"
                continue

            buffer += c
            continue

    yield buffer


def expand_macro(macroname, definitions, fallback):
    if macroname not in definitions:
        return fallback
    return definitions[macroname].value


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

    keyword, params = snippet[1:].split(" ", 1)
    if is_definition(keyword):
        parse_rpmmacros("%" + params, definitions)
        return ""

    return "TODO"


def expand_macros(snippets, definitions):
    "expand macros in parse_specfile() output"

    return [_expand_snippet(s, definitions) for s in snippets]


def expand_string(string, macros):
    """Expand macros, return string (not a generator)."""
    return "".join(list(expand_string_generator(string, macros)))


def define_tags_as_macros(line, macros):
    """Define macros from specfile tags, like %name from Name:"""
    try:
        tag_raw, definition = line.split(":", maxsplit=1)
    except ValueError:
        return
    tag = tag_raw.strip().lower()
    if tag in [
        "name",
        "release",
        "version",
        "epoch",
    ]:
        macros[tag] = definition.strip()


def expand_specfile(content, macros):
    """Expand specfile as string"""
    return "".join(expand_specfile_generator(content, macros))


def expand_specfile_generator(content, macros):
    """Expand specfile, parse Name/Version/etc."""
    buffer = ""
    for string in expand_string_generator(content, macros):
        buffer += string
        lines = deque(buffer.splitlines(keepends=True))
        if not lines:
            continue
        buffer = ""
        while lines:
            line = lines.popleft()
            if line and line[-1] == "\n":
                define_tags_as_macros(line, macros)
                yield line
            else:
                buffer = line
    yield buffer


def expand_string_generator(string, macros):
    """ expand macros in string """
    parts = list(get_parts(string, macros))
    todo = deque(parts)
    while todo:
        string = todo.popleft()
        if not string.startswith('%'):
            yield string
            continue

        if string.startswith("%global "):
            _, name, body = string.split(maxsplit=2)
            expanded_body = expand_string(body, macros)
            macros[name] = expanded_body
            yield ""
            continue

        expanded = _expand_snippet(string, macros)
        if expanded == string:
            yield string
            continue
        add = [x for x in  list(get_parts(expanded, macros)) if x != ""]
        add.reverse()
        todo.extendleft(add)
