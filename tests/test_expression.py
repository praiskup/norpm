"""
Test rpmmacro parsing in spec-files.
"""

from norpm.specfile import specfile_expand
from norpm.macro import MacroRegistry


def test_expand_expression():
    """ Normal expression expansion """
    assert specfile_expand("""\
%if 1 - 1
1
%endif
%if 1+1
2
%endif
%if 3*3/3-3 > -1
3
%endif
%if 1 && 0 || 1
4
%endif
%if 1 && 0 || 1 && 0
5
%endif
%if 1 && (0 || 1) && 1
6
%endif
%if 1 && !(0 || !1) && 1
7
%endif
""", MacroRegistry()) == """\
2
3
4
6
7
"""


def test_macro_inexpression():
    """ Normal expression expansion """
    assert specfile_expand("""\
%global foo 1
%if 1 - %foo
1
%endif
%if 1 + %foo
2
%endif
""", MacroRegistry()) == """\
2
"""


def test_with_statement():
    """ Normal expression expansion """
    assert specfile_expand("""\
%bcond_without system_ntirpc
%if 0%{?with_system_ntirpc}
1
%else
Not yet working.
%endif
""", MacroRegistry()) == """\
%bcond_without system_ntirpc
Not yet working.
"""


def test_else_and_comment():
    """ Normal expression expansion """
    assert specfile_expand("""\
%if 0
%else  # foo
1
%endif  # bar
post
""", MacroRegistry()) == """\
1
post
"""


def test_expression_expansion():
    """ Normal expression expansion """
    assert specfile_expand("%[ 1 > 2 ]\n", MacroRegistry()) == "0\n"
    assert specfile_expand("%[ 1 > 2 + 2 ]\n", MacroRegistry()) == "0\n"
    assert specfile_expand("%[ 2 + 2 ]\n", MacroRegistry()) == "4\n"
    assert specfile_expand("%[ 2 + 2 * 3 ]\n", MacroRegistry()) == "8\n"
    db = MacroRegistry()
    db["foo"] = "11"
    assert specfile_expand("%[ 2 + 2 * %foo ]\n", db) == "24\n"
    assert specfile_expand('%[ 1 ? "a" : "b" ]', MacroRegistry()) == "a"
    assert specfile_expand('%[ 0 ? "a" : "b" ]', MacroRegistry()) == "b"
    assert specfile_expand('%[ 1 + 10 ? 2 : 3 ]', MacroRegistry()) == "2"
    assert specfile_expand('%[!(0%{?rhel} >= 10)]', MacroRegistry()) == "1"


def test_expand_version_comparisons():
    """ Normal expression expansion """
    assert specfile_expand("""\
%if v"3.0" < v"5"
YES
%endif
%[ v"1:2.5" > v"3.0" ]
%[ v"1:2.5" >= v"3.0" ]
%[ v"0:2.5" == v"2.005" ]
%[ v"0:2.5" < v"1:2.5" ]
%[ v"0:2.5" <= v"1:2.5" ]
""", MacroRegistry()) == """\
YES
1
1
1
1
1
"""


def test_empty_expansion_in_epxr():
    """ Normal expression expansion """
    assert specfile_expand("""\
%[ %{?_nonexistingsomething} > -1 ]
%[ 0 || %{?_nonexistingsomething} ]
""", MacroRegistry()) == """\
1
0
"""
