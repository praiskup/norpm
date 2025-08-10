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


def test_defined():
    "test %defined macro"
    spec = """\
%dnl %define foo bar
%defined foo
%define foo bar
%{defined: foo}
end
"""
    assert specfile_expand_string(spec, MacroRegistry()) == '''\
0
1
end
'''
