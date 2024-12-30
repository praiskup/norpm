"""
Special tests for macro.py
"""

import unittest
from norpm.macro import MacroRegistry

class TestMacroCornerCases(unittest.TestCase):
    def test_invalid_name(self):
        db = MacroRegistry()
        with self.assertRaises(KeyError):
            db["ab"] = "10"
        with self.assertRaises(KeyError):
            db["100ab"] = "10"
