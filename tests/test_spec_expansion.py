""" test specfile_expand_strings() """

# pylint: disable=missing-function-docstring

import pytest

from norpm.specfile import (
    specfile_split_generator,
    specfile_expand_string,
    specfile_expand_string_generator,
    specfile_expand_strings,
    specfile_expand,
    specfile_expand_generator,
)
from norpm.macro import MacroRegistry


def test_basic_token_expansion():
    assert specfile_expand_strings(["%%", "%", " a"], {}) == ["%", "%", " a"]


def test_basic_macro_expansion():
    db = MacroRegistry()
    assert specfile_expand_strings(["%foo"], db) == ["%foo"]
    assert specfile_expand_strings(["%{foo}"], db) == ["%{foo}"]
    db["foo"] = "baz"
    assert specfile_expand_strings(["%foo"], db) == ["baz"]
    assert specfile_expand_strings(["%{foo}"], db) == ["baz"]

def test_specfile_split_generator():
    assert list(specfile_split_generator("content", {})) == ["content"]


def test_recursive_expansion():
    db = MacroRegistry()
    db["bar"] = "%content"
    db["foo"] = "%bar"
    assert "".join(list(specfile_expand_string_generator("a b %foo end", db))) == "a b %content end"


def test_multiline_expansion():
    db = MacroRegistry()
    db["bar"] = "b\nc\nd"
    db["foo"] = "%bar"
    assert "".join(list(specfile_expand_string_generator("a %foo e", db))) == "a b\nc\nd e"


def test_definition_expansion():
    db = MacroRegistry()
    db["bar"] = "content"
    assert "foo" not in db
    assert list(specfile_expand_string_generator("%define  foo %bar\n%foo", db)) == ["", "", "content"]
    assert db["foo"].value == "%bar"


def test_global_expansion():
    db = MacroRegistry()
    db["bar"] = "content"
    assert "foo" not in db
    assert list(specfile_expand_string_generator(" %global foo %bar\n%foo", db)) == [" ", "", "", "content"]
    assert db["foo"].value == "content"


def test_global_expansion_newline():
    db = MacroRegistry()
    db["bar"] = "content"
    assert "foo" not in db
    assert list(specfile_expand_string_generator(" %global foo \\\n%bar", db)) == [" ", ""]
    assert db["foo"].value == "\ncontent"


def test_specfile_expand_string():
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
    assert specfile_expand_string(" %global foo \\\n%bar\n", db) == " "
    assert db["foo"].value == "\ncontent"  # expanded!


def test_expand_underscore():
    db = MacroRegistry()
    db["_prefix"] = "/usr"
    db["_exec_prefix"] = "%_prefix"
    db["_bindir"] = "%_exec_prefix/bin"
    assert specfile_expand_string("%{_bindir}", db) == "/usr/bin"


def test_expand_parametric_definition():
    db = MacroRegistry()
    assert specfile_expand_string("%global nah(param)\\\na b c\n", db) == ""
    assert db["nah"].params == "param"


@pytest.mark.parametrize("statement", ["%define", "%global"])
def test_specfile_expand_generator(statement):
    db = MacroRegistry()
    assert specfile_expand(
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
    assert list(specfile_expand_generator(
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
    assert specfile_expand(
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
    assert specfile_expand(
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
    assert specfile_expand("%{?foo}", db) == "10"
    assert specfile_expand("%{!?foo}", db) == ""
    assert specfile_expand("%{?foo:a}", db) == "a"
    assert specfile_expand("%{!?foo:a}", db) == ""
    assert specfile_expand("%{?bar}", db) == ""
    assert specfile_expand("%{?!bar}", db) == ""
    assert specfile_expand("%{?!bar:a}", db) == "a"


def test_append_via_global():
    db = MacroRegistry()
    db["foo"] = "content"
    assert specfile_expand(
        "%global foo %foo blah\n"
        "%foo\n", db) == "content blah\n"


def test_recursion_limit():
    db = MacroRegistry()
    db["foo"] = "%bar"
    db["bar"] = "%foo"
    correct_exception = False
    try:
        specfile_expand_string("%foo", db)
    except RecursionError:
        correct_exception = True
    assert correct_exception


def test_multiline_define():
    db = MacroRegistry()
    assert specfile_expand("""\
%define blah() \\
newline
%define fooo \\\\\\
 nextline \\\\\\
  lastline
%fooo
""", db) == "nextline   lastline\n"
    assert db["blah"].value == "\nnewline"
    assert db["fooo"].value == "nextline   lastline"
