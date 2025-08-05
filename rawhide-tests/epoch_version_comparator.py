#! /usr/bin/python3

"""
Compare two files given in argv, both have format like:
    example.spec:epoch:version
"""

import logging
import sys

import yaml

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
log.addHandler(handler)


def read_file(filename):
    """
    Read file and return it as hash.
    """
    result = {}
    with open(filename, "r", encoding="utf-8") as fd:
        counter = 0
        for line in fd.readlines():
            line = line.rstrip("\n")
            counter += 1
            parts = line.split(":", 2)
            if len(parts) != 3:
                # error
                result[parts[0]] = {"error": parts[1]}
                continue
            result[parts[0]] = {
                "epoch": parts[1],
                "version": parts[2],
            }
    return result

def _main():
    original = read_file(sys.argv[1])
    output = read_file(sys.argv[2])
    with open(sys.argv[3], "r", encoding="utf-8") as fd:
        test_data = yaml.safe_load(fd)

    assert len(original) == len(output) == test_data["lines"]

    retval = 0
    correct = 0

    def _check_expected(data, expected_failures):
        exp_failure = expected_failures["errors"].get(name)
        if not exp_failure:
            # unexpected failure!
            log.error("unexpected failure")
            log.error("  %s:", name)
            for key in ["version", "epoch"]:
                value = data.get(key)
                if value is None:
                    value = "???"
                else:
                    value = value.replace("\"", "\\\"")
                log.error("    %s: \"%s\"", key, value)
            return 1
        retval = 0
        for key in ["epoch", "version"]:
            if exp_failure[key] == data[key]:
                continue

            log.error("%s: '%s' should failed with '%s', is '%s'", name,
                      key, exp_failure[key], data[key])
            retval = 1
        return retval

    for name, expected_data in original.items():
        data = output[name]
        if "error" in expected_data:
            # rpm spec failed to parse these, did we?
            seems_failing = False
            for key in ["epoch", "version"]:
                if '%' in data[key]:
                    seems_failing = True
            if seems_failing:
                if _check_expected(data, test_data):
                    retval = 1
            continue

        if "error" in data:
            if name in test_data["failures"]:
                continue
            log.error("%s: unexpected failure: %s", name, data["error"])
            retval = 1
            continue

        if data == expected_data:
            if name in test_data["failures"] or name in test_data["errors"]:
                log.error("%s: succeeds, but mentioned in expected.yaml", name)
                retval = 1
                continue
            correct += 1
            continue

        if _check_expected(data, test_data):
            retval = 1


    return retval

if __name__ == "__main__":
    sys.exit(_main())
