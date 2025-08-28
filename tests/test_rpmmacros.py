"""
Test basic rpmmacro file parsing.
"""

# pylint: disable=missing-function-docstring

from norpm.macro import MacroRegistry
from norpm.macrofile import macrofile_parse, macrofile_split_generator


def test_basicdef():
    macros = MacroRegistry()
    macrofile_parse("%foo bar", macros)
    assert macros.to_dict() == {"foo": ("bar",)}
    macrofile_parse(
        "%baz bar %{\n"
        " foo}\n",
        macros
    )
    assert macros.to_dict() == {
        "foo": ("bar",),
        "baz": ("bar %{\n foo}",),
    }
    macrofile_parse(
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
    macrofile_parse("", macros)
    assert macros.empty


def test_newline():
    macros = MacroRegistry()
    macrofile_parse(
        "%foo\\\n"
        " %bar blah\\\n"
        " and \\blah",
        macros)
    assert macros.to_dict() == {"foo": ("\n %bar blah\n and blah",)}

def test_trailing_space():
    macros = MacroRegistry()
    macrofile_parse(
        "%foo \\\n"
        " %bar blah \\\n"
        " and spaces:    	",
        macros)
    assert macros.to_dict() == {"foo": ("\n %bar blah \n and spaces:",)}


def test_backslashed():
    macros = MacroRegistry()
    macrofile_parse("%foo %{\\}\n}\n", macros)
    assert macros.to_dict() == {"foo": ("%{}\n}",)}

def test_bash_parser():
    macros = MacroRegistry()
    macrofile_parse("%foo %(echo ahoj)\n", macros)
    assert macros.to_dict() == {"foo": ("%(echo ahoj)",)}
    macrofile_parse("%bar %(\necho barcontent)\n", macros)
    assert macros["bar"].value == "%(\necho barcontent)"

def test_ignore_till_eol():
    macros = MacroRegistry()
    macrofile_parse("foo %bar baz\nblah\n%recover foo", macros)
    assert macros.to_dict() == {"recover": ("foo",)}


def test_whitespice_before_name():
    macros = MacroRegistry()
    macrofile_parse(" % bar baz", macros)
    assert macros.to_dict() == {"bar": ("baz",)}


def test_whitespace_start():
    macros = MacroRegistry()
    macrofile_parse("%test1 \\\na\n", macros)
    macrofile_parse("%test2\\\nb\n", macros)
    macrofile_parse("%test3  \\\nc\n", macros)

    assert macros["test1"].value == '\na'
    assert macros["test2"].value == '\nb'
    assert macros["test3"].value == '\nc'

def test_inspec_parser():
    parts = list(macrofile_split_generator("%foo \nblah\n", inspec=True))
    assert parts == [("foo", "\nblah", None)]

    parts = list(macrofile_split_generator("%foo() \nblah\n", inspec=True))
    assert parts == [("foo", "\nblah", "")]

    parts = list(macrofile_split_generator("%foo() \nblah	  \n", inspec=True))
    assert parts == [("foo", "\nblah", "")]

    parts = list(macrofile_split_generator("%foo(p: ) \nblah\n", inspec=True))
    assert parts == [("foo", "\nblah", "p: ")]

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
    defs = list(macrofile_split_generator(macro_def))
    len(defs) == 2
