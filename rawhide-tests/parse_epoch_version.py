#!/bin/python3

"""
Iterate over all the provided spec files, and try to parse Epoch and Version
using norpm.
"""

import copy
import glob
import os
import sys
from norpm.specfile import specfile_expand_string, specfile_expand
from norpm.macro import MacroRegistry
from norpm.macrofile import system_macro_registry

db = MacroRegistry()
db = system_macro_registry()
db.known_norpm_hacks()

db["dist"] = ""

for spec in sorted(glob.glob("/rpm-specs/*.spec")):
    sys.stderr.write(f"Doing {spec}\n")
    basename = os.path.basename(spec)
    try:
        with open(spec, "r", encoding="utf8") as fd:
            # we don't want to leak macros from one spec file to another
            temp_db = copy.deepcopy(db)
            try:
                specfile_expand(fd.read(), temp_db)
            except Exception:  # pylint: disable=broad-exception-caught
                print(f"{basename}:Unexpected error")
                continue
            epoch = "(none)"
            if "epoch" in temp_db:
                epoch = specfile_expand_string("%epoch", temp_db)
            version = specfile_expand_string("%version", temp_db)
            print(f"{basename}:{epoch}:{version}", flush=True)
    except RecursionError:
        print(f"{basename}: RecursionError", flush=True)
