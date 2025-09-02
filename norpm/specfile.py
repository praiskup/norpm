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
from dataclasses import dataclass
import re

from norpm.tokenize import tokenize, Special, BRACKET_TYPES, OPENING_BRACKETS
from norpm.macro import is_macro_character, parse_macro_call
from norpm.macrofile import macrofile_parse, macrofile_split_generator
from norpm.getopt import getopt
from norpm.logging import get_logger
from norpm.expression import eval_rpm_expr

log = get_logger()

# pylint: disable=too-many-statements,too-many-branches


class ParserHooks:
    """
    Inherit from this method, and override mehtods you find useful.
    """
    def tag_found(self, name, value, tag_raw):
        """Called when tag is found, e.g., ExclusiveArch"""


SHELL_REGEXP_HACKS = [{
    # many packages use '%(c=%{commit0}; echo ${c:0:7})'
    'regexp': re.compile(r'%\([a-zA-Z0-9_]+=[\'\"]?%{?([a-zA-Z0-9_]+)}?[\'\"]?\s*;\s'
                         r'echo\s*[\'\"]?\${[a-zA-Z0-9]+:0:([0-9]+)}[\'\"]?'),
    'method': lambda x: f'%{{sub %{{{x[1]}}} 1 {x[2]}}}',
}, {
    # a few packages use 'echo %{git_rev} | cut -c-8'
    'regexp': re.compile(r'%\(\s*echo\s*[\'\"]?%{?([a-zA-Z0-9_]+)}?[\'\"]?\s*\|\s*'
                         r'cut\s*-[cb]\s*[0-9]?-([0-9]*)'),
    'method': lambda x: f'%{{sub %{{{x[1]}}} 1 {x[2]}}}',
}]


class _Builtin:
    expand_params = True
    @classmethod
    def eval(cls, snippet, params, db):
        """evaluate the builtin, return the expanded value"""
        raise NotImplementedError


class _BuiltinUndefine(_Builtin):
    @classmethod
    def eval(cls, snippet, params, db):
        db.undefine(params[0])
        return ""


class _BuiltinDefined(_Builtin):
    @classmethod
    def eval(cls, snippet, params, db):
        return str(int(params[0] in db))


class _BuiltinDnl(_Builtin):
    expand_params = False
    @classmethod
    def eval(cls, _snippet, _params, _db):
        return ""


class _BuiltinSub(_Builtin):
    @classmethod
    def eval(cls, snippet, params, db):
        # params: string start stop (indexes)
        try:
            string, start, stop = params
            start = int(start)
            stop = int(stop)
        except ValueError:
            return snippet
        # start index to python start index
        if start >= 1:
            start -= 1
        if stop < 0:
            stop += 1
        return string[start:stop]


BUILTINS = {
    "defined": _BuiltinDefined,
    "dnl": _BuiltinDnl,
    "sub": _BuiltinSub,
    "undefine": _BuiltinUndefine,
}

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
    hooks = None
    target = None

    def __init__(self, hooks=None):
        self.condition_stack = []
        self.hooks = hooks or ParserHooks()

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


def _is_builtin(name):
    """Return true if Name is an internal name."""
    return name in BUILTINS


def specfile_split_generator(string, macros):
    """
    Split input string into a macro and non-macro parts.
    """
    context = _SpecContext()
    for s in _specfile_split_generator(context, string, macros):
        yield str(s)


@dataclass
class _Snippet:
    text: str
    in_comment: bool = False
    macro_starts_line: bool = True
    def __str__(self):
        return self.text
    def startswith(self, start):
        "bypass down to str()"
        return self.text.startswith(start)


def _specfile_split_generator(context, string, macros):

    state = "TEXT"
    depth = 0
    conditional_prefix = False
    brackets = None
    reset_comment = True
    whitespaces_starting = True
    macro_starts_line = False

    def _snippet():
        return _Snippet(buffer, in_comment=context.in_comment,
                        macro_starts_line=macro_starts_line)

    buffer = ""
    for c in tokenize(string):
        if reset_comment:
            reset_comment = False
            context.in_comment = False
            macro_starts_line = False

        if c == '#' and state != "MACRO_PARAMETRIC":
            context.in_comment = True

        if not c.isspace():
            if whitespaces_starting and c == '%':
                macro_starts_line = True
            whitespaces_starting = False

        if c == '\n' or c == Special("\n"):
            reset_comment = True
            whitespaces_starting = True

        if state == "TEXT":
            if c == Special("\n"):
                buffer += "\\\n"
                continue
            if c != "%":
                buffer += c
                continue

            yield _snippet()
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
                yield _snippet()
                state = "TEXT"
                buffer = c
                continue

            if c == "%":
                buffer += "%"
                yield _snippet()
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

            yield _snippet()
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

                yield _snippet()
                buffer = "%"
                state = "MACRO_START"
                continue

            if c in ['\t', ' ']:
                macroname = buffer[1:]
                if _is_special(macroname) or \
                        _is_builtin(macroname) or \
                        macroname in macros and macros[macroname].parametric:
                    state = "MACRO_PARAMETRIC"
                    buffer += c
                    continue

                if _is_definition(macroname):
                    state = "MACRO_DEFINITION"
                    buffer += c
                    continue

            yield _snippet()

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
                yield _snippet()
                buffer = ""
                state = "TEXT"
                continue

            buffer += c
            continue

        if state == "MACRO_PARAMETRIC":
            if c == Special('\n'):
                yield _snippet()
                buffer = ""
                state = "TEXT"
                continue
            if c == "\n":
                yield _snippet()
                if _is_condition(buffer) and macro_starts_line:
                    buffer = ""
                elif buffer.startswith("%dnl"):
                    buffer = ""
                else:
                    buffer = "\n"
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
                yield _snippet()
                # We intentionally eat the newline, and not add this
                # to the buffer. That's what RPM does.
                buffer = ""
                state = "TEXT"
                continue

            buffer += c
            continue

    yield _snippet()


def _expand_internal(context, depth, internal, params, snippet, db):
    """Return None if not internal, otherwise return expanded snippet."""
    try:
        builtin = BUILTINS[internal]
    except KeyError:
        return None
    if not context.expanding:
        return ""
    if builtin.expand_params:
        params = _specfile_expand_string(context, params, db, depth+1)
    return builtin.eval(snippet, params.split(), db)


def _parse_condition(full_snippet):
    """The snippet starts with % character.  We want to decide if this is a
    condition (or return None), and then split into left and right hand side."""

    snippet = full_snippet.text
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

    if not full_snippet.macro_starts_line:
        return None

    if snippet[terminator].isspace():
        items = snippet.split(maxsplit=1)
        if len(items) <= 1:
            raise ParseError("%if without expression")
        return (keyword, snippet[terminator:])

    if snippet[terminator] == "%":
        return (keyword, snippet[terminator:])

    return None


def _eval_expression(snippet):
    if '%' in snippet:
        return False
    if eval_rpm_expr(snippet):
        return True
    return False


class _HideAndSeekMacro:
    """
    It is rather complicated to implement a regular expression for a macro call,
    hence even in the PLY lexer.  However, we do have a norpm builtin for
    parsing macro calls, so - before we handover the string to lexer - we first
    replace macro calls with '@ID@' strings (easy to cover by regexp).
    """
    def __init__(self, context, macros, depth):
        self.lookup = []
        self.context = context
        self.macros = macros
        self.depth = depth

    def new_macro(self, macro):
        "Replace macro string with @ID@ and remember"
        new_id = len(self.lookup)
        self.lookup.append(str(macro))
        return f'@{new_id}@'

    def expand(self, string):
        "Revert %macro => @ID@ action in given string"
        for mid, mcall in enumerate(self.lookup):
            pattern = f'@{mid}@'
            # each call at most once
            string = string.replace(pattern, mcall)
        return _specfile_expand_string(self.context, string, self.macros, self.depth+1)

    def __call__(self, string):
        return self.expand(string)


def _expand_snippet(context, snippet, definitions, depth=0):
    full_snippet = snippet
    snippet = full_snippet.text

    if snippet in ['%', '%%']:
        return '%'

    if not snippet.startswith("%"):
        return snippet

    if snippet.startswith("%("):
        for hack in SHELL_REGEXP_HACKS:
            if m := hack["regexp"].match(snippet):
                return hack["method"](m)
        return snippet

    if snippet.startswith("%["):
        stripped = snippet[2:-1]
        if context.expanding:
            try:
                filtered_output = []
                hasm = _HideAndSeekMacro(context, definitions, depth)
                for part in _specfile_split_generator(context, stripped,
                                                      definitions):
                    if not part.startswith("%"):
                        filtered_output.append(str(part))
                        continue
                    filtered_output.append(hasm.new_macro(part))
                parsable = "".join(filtered_output)
                try:
                    return str(eval_rpm_expr(parsable, hasm))
                except ValueError:
                    return str(full_snippet)
            except SyntaxError:
                return snippet
        return ""

    if cond := _parse_condition(full_snippet):
        if context.in_expr:
            raise ParseError("%if %if")

        iftype, expr = cond
        # expand the expression content first
        log.debug("Expression: %s", expr)

        if context.expanding:
            context.in_expr = True
            expr = _specfile_expand_string(context, expr, definitions, depth+1)
            context.in_expr = False
            if iftype == "%if":
                try:
                    expr = _eval_expression(expr)
                except SyntaxError:
                    log.error("Failed to parse 'if' expression: %s", expr)
                    expr = False
            elif iftype in ["%ifarch", "%ifnarch"]:
                arches = expr.split()
                expr = definitions.target in arches
                if iftype == "%ifnarch":
                    expr = not expr
            else:
                expr = True  # todo arch
        else:
            expr = False

        context.condition(expr)
        return None

    cond_attempt = snippet.split()
    if cond_attempt[0] == "%else":
        context.negate_condition()
        if full_snippet.in_comment:
            return snippet
        return None

    if cond_attempt[0] == "%endif":
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

    defined = name in definitions

    if name[0] == '-' and name[1].isalpha():
        # expanding %{-m} like strings, these have special conditions
        # like %{-m:params} and %{!-m:params}
        if params and conditionals.issubset(set(['!'])):
            print_params = xor(defined, '!' in conditionals)
            return params if print_params else ""

    if '?' in conditionals:
        # params ignored
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

    if name == "expand":
        # expand params (as for every macro call), and then reexpand
        params = _specfile_expand_string(context, params, definitions, depth+1)
        return params

    if (expanded := _expand_internal(context, depth, name, params, snippet,
                                     definitions))  is not None:
        return expanded

    retval = definitions.get_macro_value(name, snippet)
    if retval == snippet:
        return retval
    if retval == "":
        return retval
    if not params:
        return retval
    if definitions[name].params is None:
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
    definitions.define("*", ' '.join(args), special=True)
    definitions.define("**", params, special=True)

    retval = _specfile_expand_string(context, retval, definitions, depth+1)

    # Undefine temporary macros
    definitions.undefine("**")
    definitions.undefine("*")
    for opt, _ in optlist:
        definitions.undefine(opt)
        definitions.undefine(opt+"*")
    definitions.undefine("#")
    for argn, _ in enumerate(args):
        definitions.undefine(str(argn+1))
    definitions.undefine("0")
    return retval


def specfile_expand_string(string, macros, depth=0):
    """Split string to snippets, and expand those that are macro calls.  This
    method returns string again.  Specfile tags are not interpreted.
    """
    context = _SpecContext()
    return _specfile_expand_string(context, string, macros, depth)


def _specfile_expand_string(context, string, macros, depth):
    return "".join(list(_specfile_expand_string_generator(context, string, macros, depth)))


def _define_tags_as_macros(context, line, macros):
    """Define macros from specfile tags, like %name from Name:"""
    try:
        tag_raw, definition = line.split(":", maxsplit=1)
    except ValueError:
        return
    tag = tag_raw.strip().lower()
    value = definition.strip()
    context.hooks.tag_found(tag, value, tag_raw)
    if tag in [
        "name",
        "release",
        "version",
        "epoch",
    ]:
        macros[tag] = value
        macros[tag.upper()] = definition.strip()


def specfile_expand(content, macros, hooks=None):
    """Expand specfile content (string), return string.  Tags (like Name:) are
    interpreted.  See specfile_expand_generator().
    """
    context = _SpecContext(hooks)
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
                _define_tags_as_macros(context, line, macros)
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
            snippet = next(generator)
            buffer = str(snippet)
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
            expanded_def = specfile_expand_string(definition, macros, depth+1)
            for name, body, params in macrofile_split_generator('%' + expanded_def, inspec=True):
                macros[name] = (body, params)
            continue

        expanded = _expand_snippet(context, snippet, macros, depth)
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
