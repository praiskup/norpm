"""
Built-in macro definitions
"""

import os

from norpm.lua import gsub


class QuotedString:
    """
    String that wouldn't be split if used as a macro parameter.  Example:
    %foo %{quote:a b  c}
    %len %foo => returns 6
    """
    def __init__(self, string):
        self.string = string
    def __str__(self):
        return self.string


class _Builtin:
    expand_params = True
    @classmethod
    def eval(cls, snippet, params, db):
        """evaluate the builtin, return the expanded value"""
        raise NotImplementedError


class _BuiltinBasename(_Builtin):
    @classmethod
    def eval(cls, snippet, params, _db):
        return os.path.basename(params[0])


class _BuiltinDirname(_Builtin):
    @classmethod
    def eval(cls, snippet, params, _db):
        return os.path.dirname(params[0])

class _BuiltinDnl(_Builtin):
    expand_params = False
    @classmethod
    def eval(cls, snippet, params, _db):
        return ""


class _BuiltinExpand(_Builtin):
    @classmethod
    def eval(cls, snippet, params, db):
        """
        Implement lua.gsub() as a macro.
        """
        return params[0]


class _BuiltinGsub(_Builtin):
    @classmethod
    def eval(cls, snippet, params, db):
        count = 0
        try:
            string = params[0]
            pattern = params[1]
            repl = params[2]
            count = int(params[3])
        except (IndexError, ValueError):
            pass
        return gsub(string, pattern, repl, count)


class _BuiltinLen(_Builtin):
    """
    Implements the %{len:...} macro builtin.

    This macro calculates the string length of the expanded value
    of its argument.
    """

    @classmethod
    def eval(cls, snippet, params, db):
        """
        Calculates the length of an expanded macro.
        """
        return str(len(params[0]))


class _BuiltinLower(_Builtin):
    @classmethod
    def eval(cls, snippet, params, db):
        return params[0].lower()


class _BuiltinQuote(_Builtin):
    """
    Implements the %{quote:...} macro builtin.

    This macro makes sure that the content is handled a single macro argument,
    even if contains spaces.
    """

    @classmethod
    def eval(cls, snippet, params, db):
        """
        Calculates the length of an expanded macro.
        """
        return QuotedString(params[0])



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


class _BuiltinUndefine(_Builtin):
    @classmethod
    def eval(cls, snippet, params, db):
        db.undefine(params[0])
        return ""

class _BuiltinUpper(_Builtin):
    @classmethod
    def eval(cls, snippet, params, db):
        return params[0].upper()



BUILTINS = {
    "basename": _BuiltinBasename,
    "dirname": _BuiltinDirname,
    "dnl": _BuiltinDnl,
    "expand": _BuiltinExpand,
    "gsub": _BuiltinGsub,
    "len": _BuiltinLen,
    "lower": _BuiltinLower,
    "quote": _BuiltinQuote,
    "sub": _BuiltinSub,
    "undefine": _BuiltinUndefine,
    "upper": _BuiltinUpper,
}
