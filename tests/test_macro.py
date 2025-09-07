"""
Special tests for macro.py
"""

import unittest
from norpm.macro import MacroRegistry, parse_macro_call as pc

# pylint: disable=missing-docstring

class TestMacroCornerCases(unittest.TestCase):
    def test_invalid_name(self):
        db = MacroRegistry()
        with self.assertRaises(KeyError):
            db["100ab"] = "10"


def test_macro_call_parser():
    assert pc("%{foo}") == (True, "foo", set(), [], None)
    assert pc("%{?foo}") == (True, "foo", {'?'}, [], None)
    assert pc("%{!foo}") == (True, "foo", {'!'}, [], None)
    assert pc("%{ !foo}") == (False, "", set(), [], None)
    assert pc("%{foo :}") == (True, "foo", set(), [':'], None)
    assert pc("%{?foo :}") == (True, "foo", {'?'}, [':'], None)
    assert pc("%{foo:param}") == (True, "foo", set(), 'param', None)
    assert pc("%{?foo:alt }") == (True, "foo", {'?'}, [], 'alt ')
    assert pc("%{?!foo: alt }") == (True, "foo", {'?', '!'}, [], ' alt ')
    assert pc("%{!foo: param }") == (True, "foo", {'!'}, ' param ', None)
    assert pc("%{?!bar}") == (True, "bar", {'?', '!'}, [], None)


def test_known_hacks():
    db = MacroRegistry()
    db.known_norpm_hacks()
    assert db["goname"].value == "NORPM_HACK_NO_GONAME"
    assert db["optflags"].value == "-O2 -g3"
