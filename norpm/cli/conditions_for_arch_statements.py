"""
Script that detects what macros are evaluated in specfile %if* conditions
leading to ExcludeArch, ExclusiveArch and BuildArch.
"""

import argparse
import copy
import glob
import json
import os
import sys
from norpm.macrofile import system_macro_registry
from norpm.specfile import (
    specfile_expand,
    specfile_detect_macro_calls_in_string,
)
from norpm.specfile import ParserHooks


def _get_parser():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--specfile-dir", help="Directory with specfiles")
    group.add_argument("--specfile", help="RPM Spec file name")
    return parser


STATEMENTS = ["exclusivearch", "excludearch", "buildarch"]


class Hooks(ParserHooks):
    """
    Gather condition expressions leading to arch-specific statements, e.g.,
    ['0%{?rhel}', 'x86_64'] for
    %if 0%{?rhel}
    %ifarch x86_64
    ExclusiveArch: %java_arches
    %endif
    endif
    """
    sniff_mode = True
    def __init__(self):
        super().__init__()
        self.strings = set()

    def tag_conditions(self, name, condition_strings):
        """ Gather the expressions """
        if name not in STATEMENTS:
            return
        self.strings |= set(condition_strings)


def _is_wanted_macro(macro_name):
    if macro_name.isdigit():
        return False
    if macro_name in [
        "defined",
        "undefined",
        "expand",
    ]:
        return False

    return True


def macro_names_needed(specfile, original_registry):
    """
    Return a set of macros needed to correctly expand the SPECFILE parts with
    arch-specific statements.
    """
    hooks = Hooks()
    registry = copy.deepcopy(original_registry)
    with open(specfile, "r", encoding="utf8") as fd:
        try:
            specfile_expand(fd.read(), registry, hooks)
        except RecursionError:
            sys.stderr.write("Recursion Error.\n")
        except SyntaxError:
            sys.stderr.write("Syntax Error.\n")
        except AttributeError:
            sys.stderr.write("Attribute Error.\n")

    strings = hooks.strings

    with open(specfile, "r", encoding="utf8") as fd:
        for line in fd.readlines():
            line = line.strip()
            if not any(line.lower().startswith(s + ":") for s in STATEMENTS):
                continue
            strings.add(line.split(":", 1)[1])

    macro_calls = set()
    for s in strings:
        macro_calls |= specfile_detect_macro_calls_in_string(s, registry)

    return {x for x in macro_calls if _is_wanted_macro(x)}


def _main():
    opts = _get_parser().parse_args()

    # read system macros
    registry = system_macro_registry()
    registry.known_norpm_hacks()
    registry["dist"] = ""
    fullset = set()

    if opts.specfile:
        the_set = macro_names_needed(opts.specfile, registry)
        print(json.dumps(sorted(the_set), indent=4))
        sys.exit(0)
    elif opts.specfile_dir:
        pattern = os.path.join(opts.specfile_dir, "*.spec")
        for spec in glob.glob(pattern):
            sys.stderr.write(f"parsing {spec}\n")
            items = macro_names_needed(spec, registry)
            if not items:
                continue
            sys.stderr.write(f"found: {items}\n")
            fullset |= items

    else:
        assert False

    print(json.dumps(sorted(fullset), indent=4))
