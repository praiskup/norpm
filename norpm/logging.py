"""
Logging configuration for norpm project.
"""

import logging

def get_logger(name=None):
    """Allocate configured logger."""
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    return log
