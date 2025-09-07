"""
Mimic lua things in python.
"""

import re


def lua_to_python_pattern(lua_pattern):
    """
    Converts a Lua pattern into a Python regex pattern.
    """

    # Mapping of Lua pattern classes to Python regex classes
    mapping = {
        '%.': '\\.',               # dot
        '%%': '__PERCENT_SIGN__',  # escaped
        '%a': r'[a-zA-Z]',         # alphabetic
        '%c': r'[\x00-\x1f\x7f]',  # control
        '%d': r'\d',               # digit
        '%l': r'[a-z]',            # lowercase
        '%p': r'[^\w\s]',          # punctuation
        '%s': r'\s',               # whitespace
        '%u': r'[A-Z]',            # uppercase
        '%w': r'\w',               # alphanumeric
        '%x': r'[0-9a-fA-F]',      # hex digit
    }

    # Handle escaped characters, especially %
    processed_pattern = lua_pattern.replace('%%', '__PERCENT_SIGN__')

    # Replace Lua's special characters with Python's
    for lua_char, py_char in mapping.items():
        processed_pattern = processed_pattern.replace(lua_char, py_char)

    if processed_pattern.startswith('+'):
        # %{gsub %version + -}
        processed_pattern = '\\+' + processed_pattern[1:]

    # Restore escaped percent signs
    return processed_pattern.replace('__PERCENT_SIGN__', '%')


def gsub(string, pattern, repl, n=0):
    """
    Simplified version of lua.gsub(), it handles just one string replacement.
    """
    py_pattern = lua_to_python_pattern(pattern)
    new_s, _ = re.subn(py_pattern, repl, string, count=n)
    return new_s
