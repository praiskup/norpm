""" test expand_macros() """

# pylint: disable=missing-function-docstring

from norpm.specfile import expand_macros
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
