"""
norpm exceptions
"""

class NorpmError(RuntimeError):
    """common ancestor for norpm exceptions"""

class NorpmSyntaxError(NorpmError):
    """RPM syntax error detected"""

class NorpmRecursionError(NorpmError):
    """Too deep macro expansion hierarchy"""

class NorpmInvalidMacroName(NorpmError):
    """Trying to define macro with a wrong name"""
