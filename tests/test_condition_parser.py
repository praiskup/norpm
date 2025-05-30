import pytest
from norpm.specfile import specfile_expand, ParseError
from norpm.macro import MacroRegistry


def test_if_else():
    db = MacroRegistry()
    assert specfile_expand("""\
%if 1
if
%else
else
%endif
""", db) == "if\n"


def test_if_else2():
    db = MacroRegistry()
    assert specfile_expand("""\
%global nil %{!?nil:}
%global foo %nil 0
%if%foo
if
%else
else
%endif
%global foo 1
%if %foo
if
%else
else
%endif
""", db) == "else\nif\n"


def test_if_else3():
    db = MacroRegistry()
    assert specfile_expand("""\
%global nil %{!?nil:}
%global foo %nil 1
%nil
""", db) == "\n"


def test_if_nested():
    with pytest.raises(ParseError):
        specfile_expand("""\
%if %if 0
what happens
%endif
""", MacroRegistry()) == "\n"


def test_else_commented():
    assert specfile_expand("""\
#%else
""", MacroRegistry()) == "#%else\n"


def test_endif_no_if():
    assert specfile_expand("""\
%endif
""", MacroRegistry()) == ""
