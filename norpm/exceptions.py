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

class NorpmNoSuchMacro(NorpmError):
    """Referenced macro is not defined"""

class NorpmMissingArgument(NorpmError):
    """Builtin macro called without a required argument"""
