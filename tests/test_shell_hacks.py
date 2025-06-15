""" Test hacks norpm has to overcome common '%()' patterns """

from norpm.specfile import specfile_expand
from norpm.macro import MacroRegistry

def test_commit_shortener():
    """ Shortening commit SHA """
    assert specfile_expand("""\
%define foo e02feaaf245528401c40dfae113e3fc424b1deef
%global short %(abc=%{foo} ; echo ${abc:0:7})
%short
%{sub %foo 2 3}%{sub %{foo} 3 2}
%{sub %foo -4 -3}
""", MacroRegistry()) == """\
e02feaa
02
de
"""
