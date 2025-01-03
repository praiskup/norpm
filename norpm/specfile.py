"""
Spec file parser
"""

from collections import deque

from norpm.tokenize import tokenize, Special
from norpm.macro import is_macro_name, is_macro_character, parse_macro_call
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
    special = {"if", "else", "endif", "setup", "package"}
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
    conditional_prefix = False

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

            if c in ['?', '!']:
                conditional_prefix = True
                buffer += c
                state = "MACRO"
                continue

            yield buffer
            state = "TEXT"
            buffer = c
            continue

        if state == "MACRO":
            if conditional_prefix and c in ['?', '!']:
                buffer += c
                continue
            conditional_prefix = False

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

    if is_special(snippet[1:]):
        return snippet

    if snippet.startswith('%define ') or snippet.startswith('%global '):
        _, params = snippet[1:].split(" ", 1)
        parse_rpmmacros("%" + params, definitions)
        return ""

    success, name, conditionals, params, alt = parse_macro_call(snippet)
    if not success:
        return snippet

    if '?' in conditionals:
        # params ignored
        defined = name in definitions
        if '!' in conditionals:
            if not alt:
                return ""
            if not defined:
                return alt
            return ""

        if defined and alt:
            return alt

        return definitions[name].value if defined else ""

    return expand_macro(name, definitions, snippet)


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


def line_ends_preamble(line):
    """Return True if the text line ends the main specfile preamble.
    """
    line = line.strip()
    terminators = [
        "prep", "build", "install", "description",
        "generate_buildrequires",
    ]
    if any(line.startswith("%"+term) for term in terminators):
        return True
    if line.startswith("%package "):
        return True
    return False


def expand_specfile_generator(content, macros):
    """Expand specfile, parse Name/Version/etc."""
    buffer = ""
    done = False
    for string in expand_string_generator(content, macros):
        if done:
            yield string
            continue
        buffer += string
        lines = deque(buffer.splitlines(keepends=True))
        if not lines:
            continue
        buffer = ""
        while lines:
            line = lines.popleft()
            if line_ends_preamble(line):
                done = True
                yield ''.join([line]+list(lines))
                continue
            if line and line[-1] == "\n":
                define_tags_as_macros(line, macros)
                yield line
            else:
                buffer = line
    yield buffer


def expand_string_generator(string, macros):
    """ expand macros in string """
    parts = [(0, x) for x in get_parts(string, macros)]
    todo = deque(parts)
    while todo:
        depth, buffer = todo.popleft()
        if not buffer.startswith('%'):
            yield buffer
            continue

        if buffer.startswith("%global "):
            _, name, body = buffer.split(maxsplit=2)
            expanded_body = expand_string(body, macros)
            macros[name] = expanded_body
            yield ""
            continue

        expanded = _expand_snippet(buffer, macros)
        if expanded == buffer:
            yield buffer
            continue

        depth += 1
        if depth >= 1000:
            raise RecursionError(f"Macro {buffer} causes recursion loop")

        add = [(depth, x) for x in list(get_parts(expanded, macros)) if x != ""]
        add.reverse()
        todo.extendleft(add)
