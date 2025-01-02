"""
Test rpmmacro parsing in spec-files.
"""

from norpm.specfile import parse_specfile
from norpm.macro import MacroRegistry

# pylint: disable=missing-function-docstring

def test_basic_spec():
    macros = MacroRegistry()
    assert parse_specfile("", macros) == []
    assert parse_specfile("%foo", macros) == ["%foo"]
    assert parse_specfile("%foo%foo", macros) == ["%foo", "%foo"]
    assert parse_specfile("%{foo}%foo", macros) == ["%{foo}", "%foo"]
    assert parse_specfile("%{foo}foo", macros) == ["%{foo}", "foo"]
    assert parse_specfile("%{bar}", macros) == ["%{bar}"]
    assert parse_specfile("%foo %{bar} %{doh}", macros) == ["%foo", " ", "%{bar}", " ", "%{doh}"]
    assert parse_specfile("% %%", macros) == ["%", " ", "%%"]
    assert parse_specfile("a %{?bar:%{configure}}", macros) == ["a ", "%{?bar:%{configure}}"]
    assert parse_specfile(" foo%bar@bar", macros) == [" foo", "%bar", "@bar"]
    assert parse_specfile("%bar%{bar}%bar", macros) == ["%bar", "%{bar}", "%bar"]
    assert parse_specfile("%@bar", macros) == ["%", "@bar"]
    assert parse_specfile("%bar{baz}", macros) == ["%bar", "{baz}"]
    assert parse_specfile("%bar{baz%bar", macros) == ["%bar", "{baz", "%bar"]


def test_parametric_line():
    macros = MacroRegistry()
    macros["foo"] = ("a %1 b", "")
    macros["bar"] = "a %1 b"
    assert macros["foo"].parametric
    assert not macros["bar"].parametric
    assert parse_specfile("%foo a b c", macros) == ["%foo a b c"]
    assert parse_specfile("%foo a b c\nb", macros) == ["%foo a b c", "\nb"]
    assert parse_specfile("%foo a %b c\\\nb", macros) == ["%foo a %b c", "b"]
    assert parse_specfile("%bar a b c", macros) == ["%bar", " a b c"]


def test_special():
    macros = MacroRegistry()
    assert parse_specfile("%if %foo", macros) == ["%if %foo"]


def test_newline():
    macros = MacroRegistry()
    assert parse_specfile(
        "abc\n"
        "%foo \n"
        "%{blah: %{foo\n"
        "}}%doh",
        macros) == ['abc\n', '%foo', ' \n',
                    '%{blah: %{foo\n}}', "%doh"]

def test_definition_parser():
    macros = MacroRegistry()
    assert parse_specfile("blah%define abc foo\n", macros) == \
            ['blah', '%define abc foo']
    assert parse_specfile(
        "%define abc foo\\\n"
        "bar baz\\\n"
        "end\n",
        macros) == ['%define abc foo\\\nbar baz\\\nend']
    assert parse_specfile(
        "%define abc %{expand:foo\n"
        "bar baz\\\n"
        "end\n}\n",
        macros) == ['%define abc %{expand:foo\nbar baz\\\nend\n}']


def test_parse_multiline_global():
    macros = MacroRegistry()
    assert parse_specfile(" %global foo \\\n%bar", macros) == [" ", "%global foo \\\n%bar"]


def test_tricky_macros():
    macros = MacroRegistry()
    assert parse_specfile(" %??!!foo ", macros) == [" ", "%??!!foo", " "]
    assert parse_specfile("%??!!foo! ", macros) == ["%??!!foo", "! "]
