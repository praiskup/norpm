""" test expand_macros() """

# pylint: disable=missing-function-docstring

from norpm.specfile import expand_macros, get_parts, expand_string
from norpm.macro import MacroRegistry


def test_basic_token_expansion():
    assert expand_macros(["%%", "%", " a"], {}) == ["%", "%", " a"]


def test_basic_macro_expansion():
    db = MacroRegistry()
    assert expand_macros(["%foo"], db) == ["%foo"]
    assert expand_macros(["%{foo}"], db) == ["%{foo}"]
    db["foo"] = "baz"
    assert expand_macros(["%foo"], db) == ["baz"]
    assert expand_macros(["%{foo}"], db) == ["baz"]

def test_get_parts():
    assert list(get_parts("content", {})) == ["content"]


def test_recursive_expansion():
    db = MacroRegistry()
    db["bar"] = "%content"
    db["foo"] = "%bar"
    assert "".join(list(expand_string("a b %foo end", db))) == "a b %content end"


def test_multiline_expansion():
    db = MacroRegistry()
    db["bar"] = "b\nc\nd"
    db["foo"] = "%bar"
    assert "".join(list(expand_string("a %foo e", db))) == "a b\nc\nd e"


def test_definition_expansion():
    db = MacroRegistry()
    db["bar"] = "content"
    assert "foo" not in db
    assert list(expand_string("%define  foo %bar\n%foo", db)) == ["", "\n", "content"]
    assert db["foo"].value == "%bar"
