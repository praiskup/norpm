"""
Parse macro file into a "macroname = unexpanded value" dictionary
"""

import logging

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)


def tokenize(string):
    """
    Return either character or special token.
    """
    backslash_mode = False
    for c in string:
        if backslash_mode:
            backslash_mode = False
            if c == "\n":
                yield "follow_line"
            else:
                yield c
        else:
            if c == '\\':
                backslash_mode = True
                continue
            yield c


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
            if c == "follow_line":
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
            if c == "follow_line":
                continue

            if c == '{':
                depth += 1
                ctx.value += c
                continue
            if depth:
                ctx.value += c
                if c == '}':
                    depth -= 1
                continue
            if c == '\n':
                macros[ctx.macroname] = (
                    ctx.params,
                    ctx.value,
                )
                _reset()
                continue

            ctx.value += c
            continue

        if ctx.state == "IGNORE_TIL_EOL":
            if c == '\n':
                _reset()
            continue

    if ctx.state == "VALUE":
        macros[ctx.macroname] = (ctx.params, ctx.value,)
