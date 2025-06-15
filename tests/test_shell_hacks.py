""" Test hacks norpm has to overcome common '%()' patterns """

from norpm.specfile import specfile_expand, SHELL_REGEXP_HACKS
from norpm.macro import MacroRegistry

def test_commit_shortener():
    """ Shortening commit SHA """
    assert specfile_expand("""\
%define foo e02feaaf245528401c40dfae113e3fc424b1deef
%global short %(abc=%{foo} ; echo ${abc:0:7})
%global short2 %(echo %{foo} | cut -c-3)
%short
%{sub %foo 2 3}%{sub %{foo} 3 2}
%{sub %foo -4 -3}
%short2
""", MacroRegistry()) == """\
e02feaa
02
de
e02
"""


def test_cut_hack():
    """Some packages use cut"""
    # $ diff -u /tmp/norpm /tmp/rpm  | grep ^- | grep cut | sed 's/[^%]*//' | sort -u
    data = """\
%(echo '%{commit}' | cut -b -7)
%(echo %{gitcommit} | cut -c 1-8)
%(echo %{git_commit} | cut -c -8)
%(echo %{git_rev} | cut -c-8)
%(echo "%{_git_rev}" | cut -c-8)
%(c="%{git_commit}"; echo "${c:0:7}")
%(c="%{git_commit}"; echo ${c:0:7})
%(c='%{git_commit}'; echo "${c:0:8}")
%(c=%{github_commit}; echo ${c:0:7})
"""
    for macro in data.splitlines():
        matched = False
        for matcher in SHELL_REGEXP_HACKS:
            if matcher["regexp"].match(macro):
                matched = True

        if not matched:
            assert "" == macro
