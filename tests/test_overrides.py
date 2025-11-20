"""
Test overrides.py
"""

import os

from norpm.macrofile import system_macro_registry
from norpm.overrides import override_macro_registry

def test_override_basic():
    """
    Classic use-case for override_macro_registry.
    """
    overrides = os.path.join(os.path.dirname(__file__),
                             "distro-arch-specific.json")
    db = system_macro_registry()
    db = override_macro_registry(db, overrides, "rhel-10")
    assert db["rhel"].value == '10'
    assert "fedora" not in db

def test_not_existing_tag(caplog):
    """Selecting an ununsed tag is just a warning"""
    overrides = os.path.join(os.path.dirname(__file__),
                             "distro-arch-specific.json")
    db = system_macro_registry()
    db = override_macro_registry(db, overrides, "wrong-tag")
    assert any('Tag "wrong-tag" is not defined in' in x for x in caplog.messages)
    # stays undefined
    assert "fedora" not in db and "rhel" not in db
