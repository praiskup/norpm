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
%if ! %{?with_system_ntirpc}
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
