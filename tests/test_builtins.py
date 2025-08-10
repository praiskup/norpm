"""
Test _Builtin statements.
"""

from norpm.specfile import specfile_expand_string
from norpm.macro import MacroRegistry

def test_dnl():
    "test %dnl expansion"
    spec = """\
%dnl %define foo bar
%foo
%dnl bar
%{dnl aaa}after
"""
    assert specfile_expand_string(spec, MacroRegistry()) == '''\
%foo\nafter
'''
