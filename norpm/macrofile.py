"""
Parse macro file into a "macroname = unexpanded value" dictionary
"""

import logging

from norpm.tokenize import tokenize, Special

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)



class _CTX():
    def __init__(self):
        self.state = "START"
        self.macroname = ""
        self.params = ""
        self.value = ""


def parse_rpmmacros(file_contents, macros):
    """
    Parse string containing '%foo bar' macro definitions.
    """
    # pylint: disable=too-many-branches,too-many-statements

    ctx = _CTX()
    ctx.state = "START"
    ctx.macroname = ""
    ctx.value = ""
    ctx.params = None
    depth = 0

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
                _reset()
                continue

            if c.isspace():
                log.debug("macro name: %s", ctx.macroname)
                ctx.state = "VALUE_START"
                continue

            if c == '(':
                ctx.state = 'PARAMS'
                continue

            ctx.macroname += c
            continue

        if ctx.state == 'PARAMS':
            if c == ')':
                ctx.state = "VALUE_START"
                continue
            ctx.params = ctx.params + c if ctx.params else c
            continue

        if ctx.state == "VALUE_START":
            if c.isspace():
                continue
            ctx.value += c
            ctx.state = "VALUE"
            continue

        if ctx.state == "VALUE":
            if c == Special("\n"):
                continue

            if c == Special('{'):
                depth += 1
                ctx.value += c
                continue
            if depth:
                if c == Special('}'):
                    depth -= 1
                    ctx.value += c
                else:
                    ctx.value += c
                continue
            if c == '\n':
                macros[ctx.macroname] = (ctx.value, ctx.params)
                _reset()
                continue

            ctx.value += c
            continue

        if ctx.state == "IGNORE_TIL_EOL":
            if c == '\n':
                _reset()
            continue

    if ctx.state == "VALUE":
        macros[ctx.macroname] = (ctx.value, ctx.params)
