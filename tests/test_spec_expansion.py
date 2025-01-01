""" test expand_macros() """

# pylint: disable=missing-function-docstring

from norpm.specfile import (
    expand_macros, get_parts, expand_string, expand_string_generator)
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
    assert "".join(list(expand_string_generator("a b %foo end", db))) == "a b %content end"


def test_multiline_expansion():
    db = MacroRegistry()
    db["bar"] = "b\nc\nd"
    db["foo"] = "%bar"
    assert "".join(list(expand_string_generator("a %foo e", db))) == "a b\nc\nd e"


def test_definition_expansion():
    db = MacroRegistry()
    db["bar"] = "content"
    assert "foo" not in db
    assert list(expand_string_generator("%define  foo %bar\n%foo", db)) == ["", "", "content"]
    assert db["foo"].value == "%bar"


def test_global_expansion():
    db = MacroRegistry()
    db["bar"] = "content"
    assert "foo" not in db
    assert list(expand_string_generator(" %global foo %bar\n%foo", db)) == [" ", "", "", "content"]
    assert db["foo"].value == "content"


def test_global_expansion_newline():
    db = MacroRegistry()
    db["bar"] = "content"
    assert "foo" not in db
    assert list(expand_string_generator(" %global foo \\\n%bar", db)) == [" ", ""]
    assert db["foo"].value == "\ncontent"


def test_expand_string():
    """
    Try this with RPM, eof is catenated with the leading a!
        cat <<EOF
        a%global foo \
        bar
        EOF
    """
    db = MacroRegistry()
    db["bar"] = "content"
    assert "foo" not in db
    assert expand_string(" %global foo \\\n%bar\n", db) == " "
    assert db["foo"].value == "\ncontent"  # expanded!


def test_expand_underscore():
    db = MacroRegistry()
    db["_prefix"] = "/usr"
    db["_exec_prefix"] = "%_prefix"
    db["_bindir"] = "%_exec_prefix/bin"
    assert expand_string("%{_bindir}", db) == "/usr/bin"
