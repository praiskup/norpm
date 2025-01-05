#!/bin/python3

"""
Expand rpm specfile, using the system macro definitions.
"""

import argparse
import sys
from norpm.macrofile import system_macro_registry
from norpm.specfile import specfile_expand, specfile_expand_string

def _get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--specfile", help="RPM Spec file name", required=True)
    parser.add_argument("--expand-string", help=(
        "Interpret the given specfile first, but don't print the expanded "
        "specfile to standard output though.  Expand additional string "
        "and print just that."
        ))
    return parser


def _main():
    parser = _get_parser()
    opts = parser.parse_args()
    registry = system_macro_registry()
    registry["dist"] = ""
    registry.known_norpm_hacks()
    try:
        with open(opts.specfile, "r", encoding="utf8") as fd:
            expanded_specfile = specfile_expand(fd.read(), registry)
        if opts.expand_string:
            if opts.expand_string[-1] != "\n":
                opts.expand_string += "\n"
            sys.stdout.write(specfile_expand_string(opts.expand_string, registry))
            return 0
        sys.stdout.write(expanded_specfile)
        return 0
    except RecursionError as exc:
        sys.stderr.write(str(exc))
    return 1


if __name__ == "__main__":
    sys.exit(_main())
