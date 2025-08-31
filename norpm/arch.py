"""
Arch specific logic.
"""

import platform


def detect_host_arch():
    """ Guess the host's architecture """
    return platform.uname().machine
