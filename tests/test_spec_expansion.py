""" test expand_macros() """

# pylint: disable=missing-function-docstring

import pytest

from norpm.specfile import (
    expand_macros, get_parts, expand_string,
    expand_string_generator, expand_specfile_generator,
    expand_specfile,
)
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


def test_expand_parametric_definition():
    db = MacroRegistry()
    assert expand_string("%global nah(param)\\\na b c\n", db) == ""
    assert db["nah"].params == "param"


@pytest.mark.parametrize("statement", ["%define", "%global"])
def test_expand_specfile_generator(statement):
    db = MacroRegistry()
    assert expand_specfile(
        "%define myname foo\n"
        "%define myversion 1.1\n"
        "Name: %myname\n"
        f"{statement} redefined %name\n"
        "Version: %myversion", db
    ) == (
        "Name: foo\n"
        "Version: 1.1"
    )
    assert db["name"].value == "foo"
    expected = "foo" if statement == "%global" else "%name"
    assert db["redefined"].value == expected


def test_invalid_tag():
    db = MacroRegistry()
    assert list(expand_specfile_generator(
        "Name: %myname\n"
        "foo\n",
        db,
    )) == [
        "Name: %myname\n",
        "foo\n", '',
    ]


def test_expand_tags_in_macro_tricky():
    """RPM itself needs to do two-pass parsing to handle this"""
    db = MacroRegistry()
    assert expand_specfile(
        "Name: %myname\n"
        "%define myname foo\n",
        db,
    ) == (
        "Name: %myname\n"
    )
    assert db["name"].value == "%myname"
    assert db["myname"].value == "foo"


@pytest.mark.parametrize("terminator", ["%package foo", "%prep"])
def test_tags_parsed_only_in_preamble(terminator):
    """RPM itself needs to do two-pass parsing to handle this"""
    db = MacroRegistry()
    assert expand_specfile(
        "%define myname python-foo\n"
        "Name: %myname\n"
        f"  {terminator} \n"
        " : hello\n"
        "preparation\n"
        "Version: 10\n",
        db,
    ) == (
        "Name: python-foo\n"
        f"  {terminator} \n"
        " : hello\n"
        "preparation\n"
        "Version: 10\n"
    )
    assert db["name"].value == "python-foo"
    assert "version" not in db


def test_cond_expand():
    db = MacroRegistry()
    db["foo"] = "10"
    assert expand_specfile("%{?foo}", db) == "10"
    assert expand_specfile("%{!?foo}", db) == ""
    assert expand_specfile("%{?foo:a}", db) == "a"
    assert expand_specfile("%{!?foo:a}", db) == ""
    assert expand_specfile("%{?bar}", db) == ""
    assert expand_specfile("%{?!bar}", db) == ""
    assert expand_specfile("%{?!bar:a}", db) == "a"


def test_append_via_global():
    db = MacroRegistry()
    db["foo"] = "content"
    assert expand_specfile(
        "%global foo %foo blah\n"
        "%foo\n", db) == "content blah\n"


def test_recursion_limit():
    db = MacroRegistry()
    db["foo"] = "%bar"
    db["bar"] = "%foo"
    correct_exception = False
    try:
        expand_string("%foo", db)
    except RecursionError:
        correct_exception = True
    assert correct_exception


def test_multiline_define():
    db = MacroRegistry()
    assert expand_specfile("""\
%define blah() \\
newline
%define fooo \\\\\\
 nextline \\\\\\
  lastline
%fooo
""", db) == "nextline   lastline\n"
    assert db["blah"].value == "\nnewline"
    assert db["fooo"].value == "nextline   lastline"
