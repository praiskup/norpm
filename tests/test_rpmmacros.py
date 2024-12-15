"""
Test basic rpmmacro file parsing.
"""

# pylint: disable=missing-function-docstring

from norpm.macrofile import parse_rpmmacros


def test_basicdef():
    macros = {}
    parse_rpmmacros("%foo bar", macros)
    assert macros == {"foo": (None, "bar")}
    parse_rpmmacros(
        "%baz bar %{\n"
        " foo}\n",
        macros
    )
    assert macros == {
        "foo": (None, "bar"),
        "baz": (None, "bar %{\n foo}"),
    }
    parse_rpmmacros(
        "%blah(p:) %x %y -p*",
        macros
    )
    assert macros == {
        "foo": (None, "bar"),
        "baz": (None, "bar %{\n foo}"),
        "blah": ("p:", "%x %y -p*"),
    }


def test_empty():
    macros = {}
    parse_rpmmacros("", macros)
    assert not macros


def test_newline():
    macros = {}
    parse_rpmmacros(
        "%foo\\\n"
        " %bar blah\\\n"
        " and \\blah",
        macros)
    assert macros == {"bar": (None, "blah and blah")}


def test_backslashed():
    macros = {}
    parse_rpmmacros("%foo %{\\}\n}\n", macros)
    assert macros == {"foo": (None, "%{}\n}")}


def test_ignore_till_eol():
    macros = {}
    parse_rpmmacros("foo %bar baz\nblah\n%recover foo", macros)
    assert macros == {"recover": (None, "foo")}


def test_whitespice_before_name():
    macros = {}
    parse_rpmmacros(" % bar baz", macros)
    assert macros == {"bar": (None, "baz")}
