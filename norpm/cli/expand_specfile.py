"""
Expand rpm specfile, using the system macro definitions.
"""

import argparse
import sys
from norpm.macrofile import system_macro_registry
from norpm.specfile import specfile_expand, specfile_expand_string
from norpm.specfile import ParserHooks


class Hooks(ParserHooks):
    """ Gather access to spec tags """
    def __init__(self):
        self.tags = {}
    def tag_found(self, name, value, _tag_raw):
        """ Gather EclusiveArch, ExcludeArch and BuildArch """
        if name == "source":
            name = "source0"
        self.tags[name] = value


def _get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("--specfile", help="RPM Spec file name", required=True)
    parser.add_argument("--expand-string", help=(
        "Interpret the given specfile first, but don't print the expanded "
        "specfile to standard output though.  Expand additional string "
        "and print just that."
        ))
    parser.add_argument("--get-tag", help=(
        "Parse specfile and extract given tag"))
    return parser


def _main():
    parser = _get_parser()
    opts = parser.parse_args()
    registry = system_macro_registry()
    registry["dist"] = ""
    registry.known_norpm_hacks()
    try:
        hooks = Hooks()
        with open(opts.specfile, "r", encoding="utf8") as fd:
            expanded_specfile = specfile_expand(fd.read(), registry, hooks)
        if opts.expand_string:
            if opts.expand_string[-1] != "\n":
                opts.expand_string += "\n"
            sys.stdout.write(specfile_expand_string(opts.expand_string, registry))
            return 0
        if opts.get_tag:
            tag = opts.get_tag.lower()
            try:
                sys.stdout.write(hooks.tags[tag] + "\n")
                return 0
            except KeyError:
                sys.stderr.write(f"Tag {tag} not found\n")
                return 1
        sys.stdout.write(expanded_specfile)
        return 0
    except RecursionError as exc:
        sys.stderr.write(str(exc))
    return 1


if __name__ == "__main__":
    sys.exit(_main())
