"""
Test %if %else context.
"""

import pytest
from norpm.specfile import _SpecContext, ParseError


def test_basic_context():
    context = _SpecContext()
    context.condition(True)      # if 1
    assert context.expanding
    context.condition(False)     # if 0
    assert not context.expanding
    context.negate_condition()   # else
    assert context.expanding
    context.close_condition()    # endif
    assert context.expanding
    context.negate_condition()   # else
    assert not context.expanding
    context.close_condition()    # endif
    assert context.expanding


def test_double_else():
    context = _SpecContext()
    context.condition(True)         # if 1
    context.negate_condition()      # else
    with pytest.raises(ParseError):
        context.negate_condition()  # else
