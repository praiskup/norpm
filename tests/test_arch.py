"""
Test arch conditions
"""

from norpm.macro import MacroRegistry
from norpm.specfile import specfile_expand


def test_ifarch():
    """ %ifarch / %ifnarch """
    db = MacroRegistry()
    db.target = "ppc64le"
    spec = '''\
%ifarch x86_64 noarch s390x
nonono
%else
ELSE
%endif
%global arches noarch ppc64le x86_64
%ifarch %arches
IF
%else
ELSE
%endif
'''
    assert specfile_expand(spec, db) == """\
ELSE
IF
"""
