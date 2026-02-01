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
    assert specfile_expand('%[ "0" ? "1" : "2" ]', MacroRegistry()) == "1"
    assert specfile_expand('%[ "1" ? "1" : "2" ]', MacroRegistry()) == "1"
    assert specfile_expand('%[ "1" + "10" ]', MacroRegistry()) == "110"
    assert specfile_expand('%[ "1" + "10" ? 1 : 0 ]', MacroRegistry()) == "1"
    assert specfile_expand('%[ "1" + "10" ? "1" : 0 ]', MacroRegistry()) == "1"


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
%[ v"0:2.5" > v"1:2.5" ]
""", MacroRegistry()) == """\
YES
1
1
1
1
1
0
"""


def test_expression_failures():
    """Exception parser raises error sometimes.  Test those."""
    assert specfile_expand('%[ "10" - "2" ]', {}) == '%[ "10" - "2" ]'


def test_empty_expansion_in_epxr():
    """ Normal expression expansion """
    db = MacroRegistry()
    db["nodejs_define_version"] = ('''\
%{expand:%%global %{1}_evr %2}
%{expand:%%global %{1}_version_diff %{gsub %2 %d+: %{quote:}}}
%{expand:%%global %{1}_version %%sub %2 %%[1 + %%{len:%2} - %%{len:%%%{1}_version_diff}]  %%{len:%2}}
%{expand:%%global %{1}_epoch %%sub %2 1 %%[%%{len:%2} - %%{len:%%%{1}_version_diff} - 1]}
''', '')

    db["nodejs_define_version2"] = ('''\
%{expand:%%global %{1}_evr %2}
%{expand:%%global %{1}_version_diff %{gsub %2 %d+: %{quote:}}}
%{expand:%%global %{1}_version %%sub %2 %%{expr:1 + %%{len:%2} - %%{len:%%%{1}_version_diff}}  %%{len:%2}}
%{expand:%%global %{1}_epoch %%sub %2 1 %%{expr:%%{len:%2} - %%{len:%%%{1}_version_diff} - 1}}
''', '')

    assert specfile_expand("""\
%nodejs_define_version foo 666:1.1.1-2
%foo_evr
%foo_epoch
%foo_version
%nodejs_define_version2 bar 1.1.1-2
%bar_evr
%bar_epoch
%bar_version
""", db) == """\





666:1.1.1-2
666
1.1.1-2





1.1.1-2

1.1.1-2
"""


def test_node_version_macro():
    """ Normal expression expansion """
    assert specfile_expand("""\
%[ %{?_nonexistingsomething} > -1 ]
%[ 0 || %{?_nonexistingsomething} ]
""", MacroRegistry()) == """\
1
0
"""


def check_expr_side_effects(text, expanded_as, defined=None,
                            not_defined=None):
    """
    Expand TEXT, check it expands as EXPANDED_AS, and check if macros DEFINED
    and NOT_DEFINED are {,not} defined.
    """
    db = MacroRegistry()
    assert specfile_expand(text, db) == expanded_as
    for check in defined or []:
        name = check[0]
        check = check[1:]
        assert name in db.db
        if check:
            value = check[0]
            check = check[1:]
            assert db[name].value == value
    for check in not_defined or []:
        name = check[0]
        assert name not in db.db


def test_expression_side_effects():
    """ Normal expression expansion """
    check_expr_side_effects('%[ "ahoj" && "pepo" && "0" ]', "0")
    check_expr_side_effects('%[ "" || "ahoj" || "pepo" ]', "ahoj")
    check_expr_side_effects('%[ %["0"] ? "left" : "right" ]', "right")
    check_expr_side_effects('%[ "0" ? "true" : "false" ]', "true")
    check_expr_side_effects('%[ 0 ? "true" : "false" ]', "false")
    check_expr_side_effects('%[ 01 ? "true" : "false" ]', "true")
    check_expr_side_effects('%[ "0" ? "%{expand:%%global foo 1}"'
                            ': "%{expand:%%global bar 1}" ]', "",
                            [["foo", "1"]], [["bar"]])
    check_expr_side_effects('%[ "" ? "%{expand:%%global foo 1}" :'
                            '"%{expand:%%global bar 1}" ]', "",
                            [["bar", "1"]], [["foo"]])
    check_expr_side_effects('%[ 0 ? "%{expand:%%global foo 1}" :'
                            '"%{expand:%%global bar 1}" ]', "",
                            [["bar", "1"]], [["foo"]])
    check_expr_side_effects('%[ 1 ? "%{expand:%%global foo 1}"'
                            ': "%{expand:%%global bar 1}" ]', "",
                            [["foo", "1"]], [["bar"]])
