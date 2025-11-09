#!/bin/python3

"""
Iterate over all the provided spec files, and try to parse fields related to
architectures.
"""

import copy
import glob
import logging
import json
import os
import re
import sys

from norpm.specfile import specfile_expand
from norpm.macro import MacroRegistry
from norpm.macrofile import system_macro_registry
from norpm.exceptions import NorpmError

db = MacroRegistry()
db = system_macro_registry()
db.known_norpm_hacks()

# no need to care about Relase tags now
db["dist"] = ""

# drop definitions of os-specific macros
db.clear("fedora")
db.clear("rhel")

# we know what we are building for, define the os macros
db.define("fedora", "43")

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
log.addHandler(handler)


RE_PATTERNS = {
    "exclusivearch": re.compile(r'^exclusivearch\s*:', re.IGNORECASE),
    "excludearch": re.compile(r'^excludearch\s*:', re.IGNORECASE),
    "buildarch": re.compile(r'^buildarch\s*:', re.IGNORECASE),
}


def find_data(spec_content, specfile, output_dict, kind="expanded"):
    """
    Modify output with found info about architectures.
    """
    to_do = {}

    for line in spec_content.splitlines():
        for key, re_pattern in RE_PATTERNS.items():
            if re_pattern.match(line):
                _, rhs = line.split(":", 1)
                rhs = rhs.strip()
                if key not in to_do:
                    to_do[key] = []
                to_do[key].append(rhs)

    if specfile not in output_dict:
        output_dict[specfile] = {}

    if to_do:
        output_dict[specfile][kind] = to_do


def _dump_file(filename, output_data):
    print(f"Dumping {filename}")
    with open(filename, "w", encoding="utf-8") as fd:
        fd.write(json.dumps(output_data, indent=4))



def _main():
    counter = 0
    output = {}
    for spec in sorted(glob.glob("/rpm-specs/*.spec")):
        counter += 1
        basename = os.path.basename(spec)
        sys.stderr.write(f"Doing {basename}\n")

        if counter % 100 == 0:
            output_file = f"/tmp/intermediary.{counter}"
            _dump_file(output_file, output)

        try:
            with open(spec, "r", encoding="utf8") as fd:
                # we don't want to leak macros from one spec file to another
                temp_db = copy.deepcopy(db)

                original_file = fd.read()

                # do raw file parsing
                find_data(original_file, basename, output, "raw")

                try:
                    parsed = specfile_expand(original_file, temp_db)
                    find_data(parsed, basename, output)
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    output[basename]["expansion_error"] = str(exc)
                    continue
        except NorpmError as err:
            print(f"{basename}: {err}", flush=True)

    _dump_file("/arch-data.json", output)


if __name__ == "__main__":
    sys.exit(_main())
