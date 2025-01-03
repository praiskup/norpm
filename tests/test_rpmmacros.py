"""
Test basic rpmmacro file parsing.
"""

# pylint: disable=missing-function-docstring

from norpm.macro import MacroRegistry
from norpm.macrofile import parse_rpmmacros


def test_basicdef():
    macros = MacroRegistry()
    parse_rpmmacros("%foo bar", macros)
    assert macros.to_dict() == {"foo": ("bar",)}
    parse_rpmmacros(
        "%baz bar %{\n"
        " foo}\n",
        macros
    )
    assert macros.to_dict() == {
        "foo": ("bar",),
        "baz": ("bar %{\n foo}",),
    }
    parse_rpmmacros(
        "%blah(p:) %x %y -p*",
        macros
    )
    assert macros.to_dict() == {
        "foo": ("bar",),
        "baz": ("bar %{\n foo}",),
        "blah": ( "%x %y -p*", "p:"),
    }

    assert macros["foo"].to_dict() == ("bar",)
    assert "foo" in macros


def test_empty():
    macros = MacroRegistry()
    parse_rpmmacros("", macros)
    assert macros.empty


def test_newline():
    macros = MacroRegistry()
    parse_rpmmacros(
        "%foo\\\n"
        " %bar blah\\\n"
        " and \\blah",
        macros)
    assert macros.to_dict() == {"foo": ("\n %bar blah\n and blah",)}


def test_backslashed():
    macros = MacroRegistry()
    parse_rpmmacros("%foo %{\\}\n}\n", macros)
    assert macros.to_dict() == {"foo": ("%{}\n}",)}


def test_ignore_till_eol():
    macros = MacroRegistry()
    parse_rpmmacros("foo %bar baz\nblah\n%recover foo", macros)
    assert macros.to_dict() == {"recover": ("foo",)}


def test_whitespice_before_name():
    macros = MacroRegistry()
    parse_rpmmacros(" % bar baz", macros)
    assert macros.to_dict() == {"bar": ("baz",)}


def test_whitespace_start():
    macros = MacroRegistry()
    parse_rpmmacros("%test1 \\\na\n", macros)
    parse_rpmmacros("%test2\\\nb\n", macros)
    parse_rpmmacros("%test3  \\\nc\n", macros)

    assert macros["test1"].value == '\na'
    assert macros["test2"].value == '\nb'
    assert macros["test3"].value == '\nc'
