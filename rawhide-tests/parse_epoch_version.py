#!/bin/python3

"""
Iterate over all the provided spec files, and try to parse Epoch and Version
using norpm.
"""

import copy
import glob
import os
import sys
from norpm.specfile import specfile_expand
from norpm.macro import MacroRegistry
from norpm.macrofile import system_macro_registry
from norpm.specfile import ParserHooks

db = MacroRegistry()
db = system_macro_registry()
db.known_norpm_hacks()

db["dist"] = ""


class Hooks(ParserHooks):
    """ Gather access to spec tags """
    def __init__(self):
        self.tags = {}
    def tag_found(self, name, value, _tag_raw):
        """ Gather EclusiveArch, ExcludeArch, BuildArch... """
        if name in ["epoch", "version"]:
            self.tags[name] = value


for spec in sorted(glob.glob("/rpm-specs/*.spec")):
    sys.stderr.write(f"Doing {spec}\n")
    basename = os.path.basename(spec)
    try:
        hooks = Hooks()
        with open(spec, "r", encoding="utf8") as fd:
            # we don't want to leak macros from one spec file to another
            temp_db = copy.deepcopy(db)
            try:
                specfile_expand(fd.read(), temp_db, hooks)
            except Exception:  # pylint: disable=broad-exception-caught
                print(f"{basename}:Unexpected error")
                continue

            epoch = "(none)"
            if "epoch" in hooks.tags:
                epoch = hooks.tags["epoch"]
            version = hooks.tags["version"]
            print(f"{basename}:{epoch}:{version}", flush=True)
    except RecursionError:
        print(f"{basename}: RecursionError", flush=True)
