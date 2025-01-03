"""
Test basic rpmmacro file parsing.
"""

# pylint: disable=missing-function-docstring

from norpm.macro import MacroRegistry
from norpm.macrofile import parse_rpmmacros, parse_rpmmacros_generator


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

def test_bash_parser():
    macros = MacroRegistry()
    parse_rpmmacros("%foo %(echo ahoj)\n", macros)
    assert macros.to_dict() == {"foo": ("%(echo ahoj)",)}
    parse_rpmmacros("%bar %(\necho barcontent)\n", macros)
    assert macros["bar"].value == "%(\necho barcontent)"

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

def test_inspec_parser():
    parts = list(parse_rpmmacros_generator("%foo \nblah\n", inspec=True))
    assert parts == [("foo", "\nblah\n", None)]

    parts = list(parse_rpmmacros_generator("%foo() \nblah\n", inspec=True))
    assert parts == [("foo", "\nblah\n", None)]

def test_forgemeta_parser():
    macro_def = """\
%forgemeta(z:isva) %{lua:
local      fedora = require "fedora.common"
local       forge = require "fedora.srpm.forge"
local     verbose =  rpm.expand("%{-v}") ~= ""
local informative =  rpm.expand("%{-i}") ~= ""
local      silent =  rpm.expand("%{-s}") ~= ""
local  processall = (rpm.expand("%{-a}") ~= "") and (rpm.expand("%{-z}") == "")
if processall then
  for _,s in pairs(fedora.getsuffixes("forgeurl")) do
    forge.meta(s,verbose,informative,silent)
  end
else
  forge.meta(rpm.expand("%{-z*}"),verbose,informative,silent)
end
}
%blah nah
"""
    defs = list(parse_rpmmacros_generator(macro_def))
    len(defs) == 2
