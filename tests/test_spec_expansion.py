""" test specfile_expand_strings() """

# pylint: disable=missing-function-docstring

import pytest

from norpm.specfile import (
    specfile_split_generator,
    specfile_expand_string,
    specfile_expand_string_generator,
    specfile_expand,
    specfile_expand_generator,
)
from norpm.macro import MacroRegistry


def _assert_expand_strings(inputs, outputs):
    for text, exp_output in zip(inputs, outputs):
        assert specfile_expand_string(text, {}) == exp_output


def test_basic_token_expansion():
    assert specfile_expand_string("%%", {}) == "%"
    assert specfile_expand_string("%", {}) == "%"
    assert specfile_expand_string("a", {}) == "a"


def test_basic_macro_expansion():
    db = MacroRegistry()
    assert specfile_expand_string("%foo", db) == "%foo"
    assert specfile_expand_string("%{foo}", db) == "%{foo}"
    db["foo"] = "baz"
    assert specfile_expand_string("%foo", db) == "baz"
    assert specfile_expand_string("%{foo}", db) == "baz"

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
    assert list(specfile_expand_string_generator("%define  foo %bar\n%foo", db)) == ["content"]
    assert db["foo"].value == "%bar"


def test_definition_expansion_trailing_newline():
    db = MacroRegistry()
    db["foo"] = "content"
    assert list(specfile_expand_string_generator("%{foo}\n", db)) == ["content", "\n"]


def test_global_expansion():
    db = MacroRegistry()
    db["bar"] = "content"
    assert "foo" not in db
    assert list(specfile_expand_string_generator(" %global foo %bar\n%foo", db)) == [" ", "content"]
    assert db["foo"].value == "content"


def test_global_expansion_newline():
    db = MacroRegistry()
    db["bar"] = "content"
    assert "foo" not in db
    assert list(specfile_expand_string_generator(" %global foo \\\n%bar", db)) == [" "]
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


def test_expand_parametric_stars():
    db = MacroRegistry()
    assert specfile_expand_string("%global nah(d:)\\\n%*\\\n%**\n"
                                  "%nah before -d d after", db) \
        == '\nbefore after\nbefore -d d after'


def test_expand_parametric_ifdefs():
    db = MacroRegistry()
    assert specfile_expand_string(
        "%define kernel_variant_package(nm:) %{?-m:1}.%{!?-m:1}.%{-m:1}.%{!-m:0}.%{?-n:1}.%{!?-n:1}.%{-n:1}.%{!-n:0}\n"
        "%kernel_variant_package\n"
        "%kernel_variant_package -m 10\n"
        "%kernel_variant_package -n 10\n"
        "%kernel_variant_package -n 10 -m 11\n", db) == (
        ".1..0..1..0\n"
        "1..1...1..0\n"
        ".1..0.1..1.\n"
        "1..1..1..1.\n"
    )


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
    assert db["NAME"].value == "python-foo"
    assert "version" not in db
    assert "VERSION" not in db


def test_version_override():
    """RPM itself doesn't override the counterpart"""
    db = MacroRegistry()
    specfile_expand(
        "Name: foo\n"
        "Version: 1.2\n"
        "%define name python-foo\n"
        "%define VERSION nah\n",
        db)
    assert db["name"].value == "python-foo"
    assert db["NAME"].value == "foo"
    assert db["version"].value == "1.2"
    assert db["VERSION"].value == "nah"


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
    assert db["foo"].value == "content blah"


def test_define_vs_global():
    """
    %global macros are expanded at the time of definition, %define macros
    are expanded at the time of calling them.
    Per docs:
    https://rpm-software-management.github.io/rpm/manual/macros.html#global-macros
    """
    db = MacroRegistry()
    db["foo"] = "content"
    assert specfile_expand(
        "%global aaa %foo blah\n"
        "%define bbb %foo blah\n"
        "%foo\n", db) == "content\n"
    assert db["aaa"].value == "content blah"
    assert db["bbb"].value == "%foo blah"


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


def test_parametric_consumption():
    """Test that parametric consume the rest of the line, while non-parametric
    keep the subsequent part of the line"""
    db = MacroRegistry()
    assert specfile_expand("""\
%define parametric() aaa
%define normal bbb
%parametric consumed
%normal kept
""", db) == "aaa\nbbb kept\n"


def test_conditional_negation():
    db = MacroRegistry()
    db["m1"] = "%{!?bar:true}"
    db["m2"] = "%{!?!bar:true}"
    db["m3"] = "%{!!?!bar:true}"
    db["m4"] = "%{!!?!!bar:true}"
    db["m5"] = "%!!?bar"
    db["m6"] = "%!!?!bar"
    assert specfile_expand_string("%m1", db) == "true"
    assert specfile_expand_string("%m2", db) == ""
    assert specfile_expand_string("%m3", db) == "true"
    assert specfile_expand_string("%m4", db) == ""
    assert specfile_expand_string("%m5", db) == ""
    assert specfile_expand_string("%m6", db) == ""
    db["bar"] = "foo"
    assert specfile_expand_string("%m1", db) == ""
    assert specfile_expand_string("%m2", db) == "true"
    assert specfile_expand_string("%m3", db) == ""
    assert specfile_expand_string("%m4", db) == "true"
    assert specfile_expand_string("%m5", db) == "foo"
    assert specfile_expand_string("%m6", db) == ""


def test_parametric_expansion_params():
    db = MacroRegistry()
    assert specfile_expand("""\
%define parametric1(b:) %{-b}  %{-b}
%define parametric2(a:) %{-x}  x%{-x}
%define parametric3(a:b) %{-a} %{-b} %{-a}
%define parametric4(a:b) %{-a} %{-b} %{-a}x
%parametric1 -b b
%parametric2 a b
%parametric3 -b -a 10
%parametric4 xyz
""", db) == """\
-b b  -b b
  x
-a 10 -b -a 10
  x
"""


def test_parametric_expansion_count():
    db = MacroRegistry()
    assert specfile_expand("""\
%define parametric1(b:) %# %0 %1 %2 %3
%parametric1 a -b b x
""", db) == """\
2 parametric1 a x %3
"""


def test_undefine():
    db = MacroRegistry()
    assert specfile_expand("""\
%define xyz first
%define xyz second
%xyz
%undefine  xyz
%xyz
%undefine xyz
%xyz
""", db) == """\
second

first

%xyz
"""

def test_if_with_newline():
    db = MacroRegistry()
    spec = b'foo\n%if 1\nif \\\n%else \nELSE \\\n%endif \npostifelse\n'.decode()
    assert specfile_expand_string(spec, db) == '''\
foo
if \\
postifelse
'''



def test_if_in_global():
    db = MacroRegistry()
    spec = '''\
%global foo \\
%if 1 \\
if \\\\\\
%else \\
ELSE \\\\\\
%endif \\
postifelse
newline
'''
    assert specfile_expand(spec, db) == """\
newline
"""

    assert db.db["foo"].value == "\nif postifelse"


def test_not_nested_expr():
    macros = MacroRegistry()
    assert specfile_expand_string("0%{?rhel} >= 6", macros) == "0 >= 6"


def test_invalid_macros():
    macros = MacroRegistry()
    assert specfile_expand_string("%{...} %?", macros) == "%{...} %?"
