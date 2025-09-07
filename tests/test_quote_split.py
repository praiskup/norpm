"""
Test the '%{quote:}' builtin.
"""

from norpm.macrofile import MacroRegistry
from norpm.specfile import _specfile_expand_string_quoted, _SpecContext


def _wrap(in_param):
    c = _SpecContext()
    db = MacroRegistry()
    return _specfile_expand_string_quoted(c, in_param, db, 0)


def test_expand_string_quoted():
    """
    Test the _specfile_expand_string_quoted method
    """
    assert _wrap("%{quote:a b c}") == ["a b c"]
    assert _wrap("a b c") == ["a", "b", "c"]
    assert _wrap(" a b c") == ["a", "b", "c"]
    assert _wrap("a b c ") == ["a", "b", "c"]
    assert _wrap(" a c ") == ["a", "c"]
    assert _wrap("%{quote:a b c}d") == ["a b cd"]
    assert _wrap("%{quote:a b c}d e") == ["a b cd", "e"]
    assert _wrap("0%{quote:a b}") == ["0a b"]
    assert _wrap("0%{quote:a b}  %{quote: c d}") == ["0a b", " c d"]
