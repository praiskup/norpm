"""
Spec file parser

Basic method / call orientation.

specfile_expand                 | entrypoint
    specfile_expand_generator   | line by line analysis of expanded string,
                                | handles Name, Version, etc.
        specfile_expand_string_generator  | gets expanded chunks
            specfile_split_generator      | returns chunks from string
            specfile_expand_string (recurses to specfile_expand_string_generator)
            _expand_snippet               | replaces %foo with value
                specfile_expand_string    | another recursion
"""

from collections import deque
from operator import xor

from norpm.tokenize import tokenize, Special, BRACKET_TYPES, OPENING_BRACKETS
from norpm.macro import is_macro_character, parse_macro_call
from norpm.macrofile import macrofile_parse, macrofile_split_generator
from norpm.getopt import getopt
from norpm.logging import get_logger

log = get_logger()

# pylint: disable=too-many-statements,too-many-branches


class ParseError(Exception):
    """General parsing error"""


class _SpecContext:
    """
    If condition is True, we produce the output.

    Attributes
    ----------

    condition_stack : list of (bool, bool) pairs.
        First bool represents original %if value.  Second bool denotes that
        %else flipped the meaning.
        The library keeps producing output (and processing nested definitions)
        as long as all the items in stack are True.
    in_expr : None or string
        Expression type, e.g., 'if'.  We can't have '%if 1 %if', e.g., this is
        to note that we are parsing `1 %if` expression.
    """

    condition_stack = None
    in_expr = None
    in_comment = None

    def __init__(self):
        self.condition_stack = []

    @property
    def expanding(self):
        """Return True if we are expanding."""
        for cond, flipped in self.condition_stack:
            if not xor(cond, flipped):
                return False
        return True

    def condition(self, expanding):
        """Nest into the stack of conditions."""
        if self.in_comment:
            return
        self.condition_stack.append((expanding, False))

    def close_condition(self):
        """Emerge from one condition level."""
        if self.in_comment:
            return
        try:
            self.condition_stack.pop()
        except IndexError:
            pass

    def negate_condition(self):
        """Revert last ondition upon %else."""
        if self.in_comment:
            return
        cond, flipped = self.condition_stack[-1]
        if flipped:
            raise ParseError("Double %else")
        self.condition_stack[-1] = (cond, True)


def specfile_split(file_contents, macros):
    """
    Parse file_contents string into a list of parts, macros and raw string
    snippets.
    """
    return [i for i in specfile_split_generator(file_contents, macros) if i != ""]


def _is_special(name):
    """Return True if the macro name is a special construct"""
    special = {"if", "else", "ifarch", "ifnarch", "endif", "setup", "package"}
    return name in special


def _is_condition(buffer):
    """Return True if the macro name condition"""
    special = {"if", "else", "ifarch", "endif"}
    for s in special:
        if not buffer.startswith("%" + s):
            continue
        if len(buffer) == len(s) + 1:
            return True
        first_after = buffer[len(s)+1]
        if first_after == "%":
            return True
        if first_after.isspace():
            return True
    return False


def _is_definition(name):
    """Return True if the Name is a macro definition keyword"""
    special = {"define", "global"}
    return name in special


def _isinternal(name):
    """Return true if Name is an internal name."""
    return name in {"undefine"}


def specfile_split_generator(string, macros):
    """
    Split input string into a macro and non-macro parts.
    """
    context = _SpecContext()
    return _specfile_split_generator(context, string, macros)


def _specfile_split_generator(context, string, macros):

    state = "TEXT"
    depth = 0
    conditional_prefix = False
    brackets = None
    reset_comment = True
    starts_whitespace = True

    buffer = ""
    for c in tokenize(string):
        if reset_comment:
            starts_whitespace = True
            reset_comment = False
            context.in_comment = False

        if c == '#' and starts_whitespace:
            context.in_comment = True

        if not c.isspace():
            starts_whitespace = False

        if c == '\n' or c == Special("\n"):
            reset_comment = True


        if state == "TEXT":
            if c != "%":
                buffer += c
                continue

            yield buffer
            buffer = c
            state = "MACRO_START"
            continue

        if state == "MACRO_START":
            if c in OPENING_BRACKETS:
                brackets = BRACKET_TYPES[str(c)]
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

            if is_macro_character(c) or c == '#':
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
                if buffer == "%if":
                    # %if%macro_that_starts_with_space
                    state = "MACRO_PARAMETRIC"
                    buffer += c
                    continue

                yield buffer
                buffer = "%"
                state = "MACRO_START"
                continue

            if c in ['\t', ' ']:
                macroname = buffer[1:]
                if _is_special(macroname) or \
                        _isinternal(macroname) or \
                        macroname in macros and macros[macroname].parametric:
                    state = "MACRO_PARAMETRIC"
                    buffer += c
                    continue

                if _is_definition(macroname):
                    state = "MACRO_DEFINITION"
                    buffer += c
                    continue

            yield buffer

            state = "TEXT"
            if c == Special("\n"):
                buffer = "\\\n"
            elif c == "\n":
                if not context.in_comment and _is_condition(buffer):
                    buffer = ""
                else:
                    buffer = "\n"
            else:
                buffer = str(c)
            continue

        if state == "MACRO_CURLY":
            if c == brackets[0]:
                depth += 1
                buffer += c
                continue

            if depth:
                if c == brackets[1]:
                    depth -= 1
                    buffer += c
                else:
                    buffer += c
                continue

            if c == brackets[1]:
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
                buffer = "" if _is_condition(buffer) else "\n"
                state = "TEXT"
                continue

            buffer += c
            continue

        if state == "MACRO_DEFINITION":
            if c == Special("\n"):
                buffer += "\n"
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


def _expand_internal(internal, params, snippet, macro_registry):
    if internal == "undefine":
        tbd = params.split()
        macro_registry.undefine(tbd[0])
        return ""
    return snippet


def _parse_condition(snippet):
    """The snippet starts with % character.  We want to decide if this is a
    condition (or return None), and then split into left and right hand side."""

    terminator = 0
    keyword = ""
    for keyword in ["%ifnarch", "%ifarch", "%if"]:
        if snippet.startswith(keyword):
            terminator = len(keyword)
            break

    if snippet == keyword:
        raise ParseError(f"{keyword} without expression")

    if terminator == 0:
        return None

    if snippet[terminator] in ["\r", "\n"]:
        raise ParseError(f"{snippet[:terminator]} without expression")

    if snippet[terminator].isspace():
        items = snippet.split(maxsplit=1)
        if len(items) <= 1:
            raise ParseError("%if without expression")
        return (keyword, snippet[terminator:])

    if snippet[terminator] == "%":
        return (keyword, snippet[terminator:])

    return None


def _eval_expression(snippet):
    if "1" in snippet:
        return True
    return False


def _expand_snippet(context, snippet, definitions, depth=0):
    if snippet in ['%', '%%']:
        return '%'

    if not snippet.startswith("%"):
        return snippet

    if snippet.startswith("%("):
        return snippet

    if cond := _parse_condition(snippet):
        if context.in_expr:
            raise ParseError("%if %if")
        _, expr = cond
        # expand the expression content first
        log.debug("Expression: %s", expr)
        context.in_expr = True
        expr = _specfile_expand_string(context, expr, definitions, depth+1)
        context.in_expr= False
        context.condition(_eval_expression(expr))
        return None

    if snippet == "%else":
        context.negate_condition()
        if context.in_comment:
            return snippet
        return None

    if snippet == "%endif":
        context.close_condition()
        return None

    if _is_special(snippet[1:]):
        return snippet

    if _isdef_start(snippet):
        if not context.expanding:
            return ""
        _, params = snippet[1:].split(maxsplit=1)
        macrofile_parse("%" + params, definitions, inspec=True)
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

    if _is_special(name):
        return snippet

    if _isinternal(name):
        return _expand_internal(name, params, snippet, definitions)

    retval = definitions.get_macro_value(name, snippet)
    if retval == snippet:
        return retval
    if retval == "":
        return retval
    if not params:
        return retval
    if not definitions[name].params:
        return retval

    # RPM also first expands the parameters before calling getopt()
    params = _specfile_expand_string(context, params, definitions, depth+1)

    # TODO: unexpanded '%foo %(shell hack)', do this better
    if params.startswith('%'):
        return retval

    optlist, args = getopt(params.split(), definitions[name].params)

    # Temporarily define '%1', '%*', '%-f', etc.
    for opt, arg in optlist:
        definitions.define(opt, opt + (" " + arg if arg else ""), special=True)
        definitions.define(opt + '*', arg, special=True)
    for argn, arg in enumerate(args):
        definitions.define(str(argn+1), arg, special=True)
    definitions.define("#", str(len(args)), special=True)
    definitions.define("0", name, special=True)

    retval = _specfile_expand_string(context, retval, definitions, depth+1)

    # Undefine temporary macros
    for opt, _ in optlist:
        definitions.undefine(opt)
        definitions.undefine(opt+"*")
    definitions.undefine("#")
    for argn, _ in enumerate(args):
        definitions.undefine(str(argn+1))
    definitions.undefine("0")
    return retval


def specfile_expand_strings(snippets, definitions):
    """Given specfile snippets (list of strings, output from
    specfile_split_generator typically), expand the snippets that seem to be
    macro calls.
    """
    context = _SpecContext()
    return  _specfile_expand_strings(context, snippets, definitions)


def _specfile_expand_strings(context, snippets, definitions):
    return [_expand_snippet(context, s, definitions) for s in snippets]


def specfile_expand_string(string, macros, depth=0):
    """Split string to snippets, and expand those that are macro calls.  This
    method returns string again.  Specfile tags are not interpreted.
    """
    context = _SpecContext()
    return _specfile_expand_string(context, string, macros, depth)


def _specfile_expand_string(context, string, macros, depth):
    return "".join(list(_specfile_expand_string_generator(context, string, macros, depth)))


def _define_tags_as_macros(line, macros):
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
        macros[tag.upper()] = definition.strip()


def specfile_expand(content, macros):
    """Expand specfile content (string), return string.  Tags (like Name:) are
    interpreted.  See specfile_expand_generator().
    """
    context = _SpecContext()
    return _specfile_expand(context, content, macros)


def _specfile_expand(context, content, macros):
    return "".join(_specfile_expand_generator(context, content, macros))


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


def specfile_expand_generator(content, macros):
    """Generator method.  Expand specfile content (string), and yield parts as
    they are interpreted and expanded. The specfile preamble is parsed
    line-by-line, and if tags like Name/Version/Epoch/etc. are observed,
    corresponding (%name, %version, %release, ...) macros are defined.
    """
    context = _SpecContext()
    return _specfile_expand_generator(context, content, macros)


def _specfile_expand_generator(context, content, macros):
    buffer = ""
    done = False
    for string in _specfile_expand_string_generator(context, content, macros):
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
                _define_tags_as_macros(line, macros)
                yield line
            else:
                buffer = line
    yield buffer


def _isdef_start(string, keywords=None):
    if keywords is None:
        keywords = ["global", "define"]
    for pfx in keywords:
        pfx = "%" + pfx
        if string.startswith(pfx):
            if string[len(pfx):][0] in ["\t", " "]:
                return True
    return False


def specfile_expand_string_generator(string, macros, depth=0):
    """Split the string to snippets, and expand parts that are macro calls."""
    context = _SpecContext()
    return _specfile_expand_string_generator(context, string, macros, depth)


def _specfile_expand_string_generator(context, string, macros, depth=0):
    string_generator = _specfile_split_generator(context, string, macros)
    todo = [(depth, string_generator)]

    while todo:
        depth, generator = todo[-1]
        try:
            buffer = next(generator)
        except StopIteration:
            todo.pop()
            continue

        if buffer == "":
            continue

        if not buffer.startswith('%'):
            if context.expanding:
                yield buffer
            continue

        if _isdef_start(buffer, ["global"]):
            if not context.expanding:
                continue

            _, definition = buffer.split(maxsplit=1)
            for name, body, params in macrofile_split_generator('%' + definition, inspec=True):
                expanded_body = _specfile_expand_string(context, body, macros, depth+1)
                macros[name] = (expanded_body, params)
            continue

        expanded = _expand_snippet(context, buffer, macros, depth)
        if expanded is None or expanded == "":
            continue

        if expanded == buffer:
            if context.expanding:
                yield buffer
            continue

        if depth >= 1000:
            raise RecursionError(f"Macro {buffer} causes recursion loop")

        new_generator = _specfile_split_generator(context, expanded, macros)
        todo.append((depth+1, new_generator))
