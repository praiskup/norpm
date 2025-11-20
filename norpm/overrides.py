"""
Tooling to manage override for MacroRegistry
"""

import copy
import json

from norpm.logging import get_logger

log = get_logger()


def _get_overrides_from_file(filename):
    with open(filename, 'r', encoding="utf8") as f:
        file_data = json.load(f)
    return file_data


def override_macro_registry(original_registry, overrides_filename, tag):
    """
    Get a copy of REGISTRY with applied TAG overrides from OVERRIDES_FILENAME.

    The format of the OVERRIDES_FILENAME is a dictionary (key-value pairs),
    where key is the macro name being overridden, and the value is a list of
    overrides.  Each override is a dictionary with `definition` field
    (with value/params) and `tags` (tag may be a distribution name).
    """
    registry = copy.deepcopy(original_registry)
    registry.known_norpm_hacks()
    overrides = _get_overrides_from_file(overrides_filename)

    def _warn_once(message):
        if hasattr(_warn_once, "warned"):
            return
        setattr(_warn_once, "warned", True)
        log.warning(message)

    for macroname in overrides.keys():
        # No matter if defined for given TAG, we undefine the macro.
        # Think of `%fc43` macro for F44 TAG on F43 host.
        registry.undefine(macroname)
        found = False
        for data in overrides[macroname]:
            if tag in data["tags"]:
                found = True
                if data["definition"] is None:
                    continue
                definition = data["definition"]
                if definition["params"] is None:
                    registry.define(macroname, definition["value"])
                else:
                    registry.define(macroname, (definition["value"],
                                                definition["params"]))
        if not found:
            _warn_once(f"Tag \"{tag}\" is not defined in "
                       f"\"{overrides_filename}\" database, macros "
                       "have unexpected values!")

    return registry
