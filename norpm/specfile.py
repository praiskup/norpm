"""
Spec file parser
"""

from norpm.tokenize import tokenize, Special
from norpm.macro import is_macro_name

# pylint: disable=too-many-statements,too-many-branches

def parse_specfile(file_contents, _macros):
    """
    Parse file_contents string into a list of parts, macros and raw string
    snippets.
    """
    parsed = []
    state = "TEXT"
    depth = 0

    buffer = ""
    for c in tokenize(file_contents):
        if state == "TEXT":
            if c != "%":
                buffer += c
                continue

            parsed.append(buffer)
            buffer = c
            state = "MACRO"
            continue

        if state == "MACRO":
            if c == Special("{"):
                buffer += c
                state = "MACRO_CURLY"
                continue

            if c.isspace():
                parsed.append(buffer)
                state = "TEXT"
                buffer = c
                continue

            if c == "%":
                buffer += "%"
                parsed.append(buffer)
                buffer = ""
                state = "TEXT"
                continue

            buffer += c
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
                parsed.append(buffer)
                buffer = ""
                state = "TEXT"
                continue

            buffer += c
            continue

    if state == "MACRO":
        parsed.append(buffer)

    return [x for x in parsed if x != '']


def expandMacro(macroname, definitions, fallback):
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
            return expandMacro(snippet[2:-1], definitions, snippet)
        return "TODO"

    if is_macro_name(snippet[1:]):
        return expandMacro(snippet[1:], definitions, snippet)

    return "TODO"


def expand_macros(snippets, definitions):
    "expand macros in parse_specfile() output"
    return [_expand_snippet(s, definitions) for s in snippets]


# %macro
# %{macro}
# %%
# %{?foo:1}
# %{!?foo:1}
# %define foo bar
# %global foo bar

# %<foo>
#   %define|%global|%if ...
# %{ }
