#! /usr/bin/python3

"""
Run tests.
"""

import copy
import json
import logging
import os
import sys

import yaml

from norpm.macrofile import system_macro_registry
from norpm.overrides import override_macro_registry
from norpm.specfile import specfile_expand, ParserHooks

SPEC_DIR = "/src/extracted_artifacts/rpm-specs"
ARCHES_DIR = "/src/extracted_artifacts//rpm-specs-arches"
SPEC_LIST = "/src/extracted_artifacts/some-exclusion-found.txt"
OVERRIDES = "/distro-arch-specific.json"

LOG = logging.getLogger("arch-test")
LOG.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
handler.setFormatter(formatter)
LOG.addHandler(handler)


class _TagHooks(ParserHooks):
    """ Gather access to spec tags """
    def __init__(self):
        self.tags = {
            "exclusivearch": [],
            "excludearch": [],
            "buildarch": [],
        }

    def tag_found(self, name, value, _tag_raw):
        """
        Parser hook that gathers the tags' values, if defined.
        """
        if name not in self.tags:
            return
        LOG.debug("Appending: %s = %s", name, value)
        self.tags[name].append(value)


def check_one(specfile, registry, expected_failures):
    """
    Extract ExclusiveArch, ExcludeArch and BuildArch, and compare with
    the given output.
    """

    hooks = _TagHooks()
    with open(os.path.join(SPEC_DIR, specfile), "r", encoding="utf8") as fd:
        specfile_expand(fd.read(), registry, hooks)
    with open(os.path.join(ARCHES_DIR, specfile + ".json"), "r",
              encoding="utf8") as fdj:
        exp = json.load(fdj)

    retval = True
    for key, value in exp.items():
        if key == 'error':
            continue
        if key not in hooks.tags:
            LOG.error("%s failure on key=%s, expected_failure = %s, "
                      "found = NOTHING", specfile, key, value)
            retval = False
            continue

        value = sorted(value)
        found = sorted(hooks.tags[key])
        exp_failure = specfile in expected_failures and \
            key in expected_failures[specfile]

        if value != found:
            if exp_failure:
                exp_fail = sorted(expected_failures[specfile][key])
                if exp_fail == found:
                    continue
                LOG.error("%s failure on key=%s, expected_failure = %s,"
                          "found = %s", specfile, key, exp_fail, found)
                retval = False
                continue

            LOG.error("%s failure on key=%s, expected = %s, found = %s",
                      specfile, key, value, found)
            retval = False
        elif exp_failure:
            LOG.error("Unexpected pass on %s key=%s", specfile, key)
            retval = False

    return retval


def process_exclusions(filepath):
    """
    Go through all the specfiles with ExcludeArch/ExclusiveArch statements.
    """
    retval = 0

    if not os.path.exists(filepath):
        LOG.fatal("File %s not found", filepath)
        sys.exit(1)

    destination = None
    registry = system_macro_registry()
    if len(sys.argv) < 3:
        LOG.fatal("missing arguments")
        sys.exit(1)

    destination = sys.argv[1]
    registry = override_macro_registry(registry, OVERRIDES, destination)
    with open(sys.argv[2], "r", encoding="utf-8") as fd:
        expected_failures = yaml.safe_load(fd)

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                filename = line.strip()
                LOG.info("Checking %s", filename)
                if not filename:
                    continue
                if not check_one(filename, copy.deepcopy(registry),
                                 expected_failures):
                    retval = 1

    except Exception:  # pylint: disable=broad-exception-caught
        LOG.exception("Error when reading files.")
        sys.exit(1)

    return retval


if __name__ == "__main__":
    sys.exit(process_exclusions(SPEC_LIST))
