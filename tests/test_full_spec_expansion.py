"""
Test larger spec files & the expected output.
"""

import os
from norpm.specfile import specfile_expand
from norpm.macro import MacroRegistry

DATADIR = os.path.join(os.path.dirname(__file__), "full_spec_expansion")


def _read_file(filename):
    with open(os.path.join(DATADIR, filename), "r") as fd:
        return fd.read()


def _write_file(filename, string):
    with open(os.path.join(DATADIR, filename), "w") as fd:
        fd.write(string)


def _test_file(filename):
    db = MacroRegistry()
    db.define("fedora", "43")
    expanded = specfile_expand(_read_file(filename), db)
    _write_file(filename + ".out", expanded)
    if expanded != _read_file(filename + ".exp"):
        raise RuntimeError(f"vim -d {DATADIR}/{filename}.out {DATADIR}/{filename}.exp")


def test_specfile_nest():
    """
    Nest has a nice global definition.
    """
    _test_file("nest.spec")


def test_specfile_clustershell():
    """
    Clustershell has %else in changelog.
    """
    _test_file("clustershell.spec")


def test_specfile_2024_cli():
    """Else statements with suffix comments"""
    _test_file("2048-cli.spec")
