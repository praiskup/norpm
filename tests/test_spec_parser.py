"""
Test rpmmacro parsing in spec-files.
"""

from norpm.specfile import specfile_split
from norpm.macro import MacroRegistry

# pylint: disable=missing-function-docstring

def test_basic_spec():
    macros = MacroRegistry()
    assert specfile_split("", macros) == []
    assert specfile_split("%foo", macros) == ["%foo"]
    assert specfile_split("%foo%foo", macros) == ["%foo", "%foo"]
    assert specfile_split("%{foo}%foo", macros) == ["%{foo}", "%foo"]
    assert specfile_split("%{foo}foo", macros) == ["%{foo}", "foo"]
    assert specfile_split("%{bar}", macros) == ["%{bar}"]
    assert specfile_split("%foo %{bar} %{doh}", macros) == ["%foo", " ", "%{bar}", " ", "%{doh}"]
    assert specfile_split("% %%", macros) == ["%", " ", "%%"]
    assert specfile_split("a %{?bar:%{configure}}", macros) == ["a ", "%{?bar:%{configure}}"]
    assert specfile_split(" foo%bar@bar", macros) == [" foo", "%bar", "@bar"]
    assert specfile_split("%bar%{bar}%bar", macros) == ["%bar", "%{bar}", "%bar"]
    assert specfile_split("%@bar", macros) == ["%", "@bar"]
    assert specfile_split("%bar{baz}", macros) == ["%bar", "{baz}"]
    assert specfile_split("%bar{baz%bar", macros) == ["%bar", "{baz", "%bar"]


def test_parametric_line():
    macros = MacroRegistry()
    macros["foo"] = ("a %1 b", "")
    macros["bar"] = "a %1 b"
    assert macros["foo"].parametric
    assert not macros["bar"].parametric
    assert specfile_split("%foo a b c", macros) == ["%foo a b c"]
    assert specfile_split("%foo a b c\nb", macros) == ["%foo a b c", "\nb"]
    assert specfile_split("%foo a %b c\\\nb", macros) == ["%foo a %b c", "b"]
    assert specfile_split("%bar a b c", macros) == ["%bar", " a b c"]


def test_special():
    macros = MacroRegistry()
    assert specfile_split("%if %foo", macros) == ["%if %foo"]


def test_newline():
    macros = MacroRegistry()
    assert specfile_split(
        "abc\n"
        "%foo \n"
        "%{blah: %{foo\n"
        "}}%doh",
        macros) == ['abc\n', '%foo', ' \n',
                    '%{blah: %{foo\n}}', "%doh"]
    assert specfile_split("%2\\\n", macros) == ['%2', '\\\n']

def test_definition_parser():
    macros = MacroRegistry()
    assert specfile_split("blah%define abc foo\n", macros) == \
            ['blah', '%define abc foo']
    assert specfile_split(
        "%define abc foo\\\n"
        "bar baz\\\n"
        "end\n",
        macros) == ['%define abc foo\nbar baz\nend']
    assert specfile_split(
        "%define abc %{expand:foo\n"
        "bar baz\\\n"
        "end\n}\n",
        macros) == ['%define abc %{expand:foo\nbar baz\nend\n}']


def test_parse_multiline_global():
    macros = MacroRegistry()
    assert specfile_split(" %global foo \\\n%bar", macros) == [" ", "%global foo \n%bar"]
    assert specfile_split(" %global foo \\\\\\\n%bar", macros) == [" ", "%global foo \\\n%bar"]
    macros = MacroRegistry()
    assert specfile_split(" %define foo \\\\\\\n%bar", macros) == [" ", "%define foo \\\n%bar"]


def test_tricky_macros():
    macros = MacroRegistry()
    assert specfile_split(" %??!!foo ", macros) == [" ", "%??!!foo", " "]
    assert specfile_split("%??!!foo! ", macros) == ["%??!!foo", "! "]
    assert specfile_split("%??!!foo: ", macros) == ["%??!!foo", ": "]


def test_parse_tabelators():
    macros = MacroRegistry()
    assert specfile_split("%global\tfoo\t\tbar\n", macros) == ["%global\tfoo\t\tbar"]
