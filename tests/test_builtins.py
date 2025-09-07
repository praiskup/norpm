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
%define defined() %{expand:%%{?%{1}:1}%%{!?%{1}:0}}
%defined foo
%define foo bar
%{defined:foo}
%{defined: foo}
end
"""
    assert specfile_expand_string(spec, MacroRegistry()) == '''\
0
1
%{? foo:1}%{!? foo:0}
end
'''


def test_text_subst_builtins():
    """ Test built-in substitution """
    spec = """\
%global text  Hello   World
%len %text
%{len:%text}
%{len: %text }
"""
    assert specfile_expand_string(spec, MacroRegistry()) == """\
5
13
15
"""


def test_gsub():
    "test %gsub macro"
    spec = """\
%define foo %{quote:hello world. I like you!}
%define bar %{gsub %foo hello hi}
%define baz %{gsub %foo %w+ X}
%bar
%{gsub %foo o X}
%{gsub %foo o X 1}
%{gsub %foo %w X 1}
%{gsub %foo %w+ X}
%{len:%baz}
%{len %baz}
%{gsub %foo %. !}
%{gsub %foo . _}
%{gsub 1.2.3 %. %{quote:}}
%{gsub 0.4.5+gimp3rc1 + -}
"""
    assert specfile_expand_string(spec, MacroRegistry()) == '''\
hi world. I like you!
hellX wXrld. I like yXu!
hellX world. I like you!
Xello world. I like you!
X X. X X X!
11
1
hello world! I like you!
________________________
123
0.4.5-gimp3rc1
'''


def test_upper_lower():
    """
    Test %upper and %lower.
    """
    spec = """\
%global text Hello   World
%{upper %text}
%{upper:%text}
%{lower:%text}
"""
    assert specfile_expand_string(spec, MacroRegistry()) == """\
HELLO
HELLO   WORLD
hello   world
"""


def test_basename_dirname():
    """
    Test %basename and %dirname.
    """
    spec = """\
%{dirname:./ahoj}
%{dirname:/bc/../ahoj}
%{dirname:/a/b/c/ahoj.txt}
%{dirname:/foo.xml}
%{basename:./ahoj}
%{basename:/bc/../ahoj}
%{basename:/a/b/c/ahoj.txt}
%{basename:/foo.xml}
"""
    assert specfile_expand_string(spec, MacroRegistry()) == """\
.
/bc/..
/a/b/c
/
ahoj
ahoj
ahoj.txt
foo.xml
"""
