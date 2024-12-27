"""
Test rpmmacro parsing in spec-files.
"""

from norpm.specfile import parse_specfile

# pylint: disable=missing-function-docstring

def test_basic_spec():
    macros = {}
    assert parse_specfile("", macros) == []
    assert parse_specfile("%foo", macros) == ["%foo"]
    assert parse_specfile("%{bar}", macros) == ["%{bar}"]
    assert parse_specfile("%foo %{bar} %{doh}", macros) == ["%foo", " ", "%{bar}", " ", "%{doh}"]
    assert parse_specfile("% %%", macros) == ["%", " ", "%%"]
    assert parse_specfile("a %{?bar:%{configure}}", macros) == ["a ", "%{?bar:%{configure}}"]


def test_newline():
    macros = {}
    assert parse_specfile(
        "abc\n"
        "%foo \n"
        "%{blah: %{foo\n"
        "}}%doh",
        macros) == ['abc\n', '%foo', ' \n',
                    '%{blah: %{foo\n}}', "%doh"]
