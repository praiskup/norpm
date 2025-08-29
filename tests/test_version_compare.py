"""
Test the version comparators.
"""

from norpm.versions import rpmvercmp, rpmevrcmp


def test_version_comparison():
    """
    Runs a comprehensive set of version comparison tests using assert.
    """

    assert rpmvercmp('1.0', '1.0') == 0, "Equality"
    assert rpmvercmp('2.5-1', '2.5-1') == 0, "Equality with release"

    assert rpmvercmp('1', '2') < 0, "Simple numeric less"
    assert rpmvercmp('2', '1') > 0, "Simple numeric greater"
    assert rpmvercmp('1.2', '1.10') < 0, "Multi-digit numeric less"
    assert rpmvercmp('1.10', '1.2') > 0, "Multi-digit numeric greater"

    assert rpmvercmp('1.0', '1.0.1') < 0, "Prefix less"
    assert rpmvercmp('1.0.1', '1.0') > 0, "Prefix greater"
    assert rpmvercmp('2.5', '2.5.1') < 0, "Prefix less 2"

    assert rpmvercmp('1.05', '1.5') == 0, "Leading zero equal"
    assert rpmvercmp('2.001', '2.1') == 0, "Multiple leading zeros equal"
    assert rpmvercmp('1.06', '1.5') > 0, "Leading zero greater"
    assert rpmvercmp('1.4', '1.05') < 0, "Leading zero less"

    assert rpmvercmp('a', 'b') < 0, "Simple alpha less"
    assert rpmvercmp('b', 'a') > 0, "Simple alpha greater"
    assert rpmvercmp('1.0a', '1.0b') < 0, "Release alpha less"
    assert rpmvercmp('beta', 'alpha') > 0, "Word alpha greater"

    assert rpmvercmp('1.0', '1.0a') < 0, "Alpha suffix makes it newer"
    assert rpmvercmp('1.0a', '1.0') > 0, "Alpha suffix makes it newer"
    assert rpmvercmp('1a2', '1a10') < 0, "Mixed alpha-numeric less"
    assert rpmvercmp('1a10', '1a2') > 0, "Mixed alpha-numeric greater"
    assert rpmvercmp('1b', '1aa') > 0, "Beta is newer"

    assert rpmvercmp('1.0~rc1', '1.0') < 0, "Tilde is always older"
    assert rpmvercmp('1.0', '1.0~rc1') > 0, "Tilde is always older"
    assert rpmvercmp('1.0~rc2', '1.0~rc1') > 0, "Tilde versions compare normally"
    assert rpmvercmp('1.0~beta', '1.0~alpha') > 0, "Tilde with alpha"

    assert rpmvercmp('1.0_1', '1.0.1') == 0, "Underscore delimiter"
    assert rpmvercmp('1..2', '1.2') == 0, "Multiple delimiters"

    assert rpmvercmp('1.0-2', '1.0-1') > 0, "Release number comparison"
    assert rpmvercmp('5.0.1', '5.0') > 0, "Patch version greater"
    assert rpmvercmp('10a', '10.1') < 0, "Alpha vs numeric segment"
    assert rpmvercmp('10.1', '10a') > 0, "Numeric vs alpha segment"
    assert rpmvercmp("1.0b", "1.0") > 0, "Complex alpha suffix"

    assert rpmvercmp('1.0^1', '1.0~1') > 0, "Caret is newer than tilde"
    assert rpmvercmp('1.0~rc1', '1.0^1') < 0, "Tilde is older than caret"

    assert rpmvercmp('1.0', '1.0^1') < 0, "Base version is older than caret version"
    assert rpmvercmp('1.0.1', '1.0^1') > 0, "Caret has lower precedence than a numeric sub-version"
    assert rpmvercmp('1.0a', '1.0^1') > 0, "Caret has lower precedence than an alpha suffix"
    assert rpmvercmp('1.1', '1.0^1') > 0, "Caret version is newer than a minor version bump"

    assert rpmvercmp('2.0', '1.0^1') > 0, "Major version bump is newer than a prior version's caret"

    assert rpmvercmp('1.0^2~beta', '1.0^2') < 0, "Pre-release of a post-release is older than the post-release itself"
    assert rpmvercmp('1.0^2', '1.0^2~beta') > 0, "Post-release is newer than its own pre-release"
    assert rpmvercmp('1.0^2~alpha', '1.0^1~gamma') > 0, "A pre-release of a newer post-release is still newer"
    assert rpmvercmp('1.0^1~rc', '1.0^1~beta') > 0, "Comparing two different pre-releases of the same post-release"

    # These are rather weird.  The version comparator ignores delimiters.
    assert rpmvercmp('1.0.^-1', '1.0^1') == 0, "Multiple delimiters around caret are ignored"
    assert rpmvercmp('-1.0', '1.0') == 0, "Leading garbage"
    assert rpmvercmp('1.0-', '1.0') == 0, "Trailing garbage"
    assert rpmvercmp('1.0-^1', '1.0^1') == 0, "Delimiters around caret are ignored"
    assert rpmvercmp('1.0-1', '1.0.1') == 0, "Delimiter equivalence"


def test_epoch_handling():
    """
    Test cases focused specifically on the parsing and comparison of the Epoch.
    """
    assert rpmevrcmp("2:1.0-1", "1:2.0-1") == 1, "Epoch '2' is newer than epoch '1'"
    assert rpmevrcmp("10:1.0-1", "9:1.0-1") == 1, "Multi-digit epoch comparison"
    assert rpmevrcmp("0:1.0-1", "1.0-1") == 0, "Explicit epoch 0 is equal to an implicit epoch 0"
    assert rpmevrcmp("1.0-1", "0:1.0-1") == 0, "Implicit epoch 0 is equal to an explicit epoch 0"
    assert rpmevrcmp("1:1.0-1", "foo:2.0-1") == 1, "Valid epoch '1' wins over invalid epoch 'foo' (treated as 0)"
    assert rpmevrcmp("1:1.0~rc1-1", "0:1.0-1") == 1, "Epoch wins over a tilde in the version"
    assert rpmevrcmp("1:1.0-1", "0:1.0^99-1") == 1, "Epoch wins over a caret in the version"
    assert rpmevrcmp("1:1.0-1~rc", "0:1.0-1^patch") == 1, "Epoch wins over tilde and caret in the release"
    assert rpmevrcmp("1:1.0-1", "0:2.0-1") == 1, "Explicit epoch is higher"
    assert rpmevrcmp("1:1.0-1", "2.0-1") == 1, "Explicit epoch vs. implicit epoch 0"
    assert rpmevrcmp("2.0-1", "1:1.0-1") == -1, "Implicit epoch 0 vs. explicit epoch"
    assert rpmevrcmp("0:1.0-1", "1.0-1") == 0, "Explicit epoch 0 is equal to implicit epoch 0"
    assert rpmevrcmp("1.0.2-1", "1.0.1-1") == 1, "Numeric version segment is higher"
    assert rpmevrcmp("1.0b-1", "1.0a-1") == 1, "Alphabetic version segment is higher"
    assert rpmevrcmp("1.0.1", "1.0-1") == 1, "Version '1.0.1' is newer than version '1.0'"
    assert rpmevrcmp("1.0-1", "1.0.1") == -1, "Version '1.0' is older than version '1.0.1'"
    assert rpmevrcmp("1.0-2", "1.0-1") == 1, "Numeric release is higher"
    assert rpmevrcmp("1.0-1b", "1.0-1a") == 1, "Alphabetic release is higher"
    assert rpmevrcmp("1.0-10", "1.0-2") == 1, "Multi-digit numeric release is handled correctly"
    assert rpmevrcmp("1.0-1", "1.0") == 1, "A version with a release is newer than one without"
    assert rpmevrcmp("1.0", "1.0-1") == -1, "A version without a release is older"
    assert rpmevrcmp("1.0~rc1-1", "1.0-1") == -1, "Tilde in version makes it a pre-release"
    assert rpmevrcmp("1.0-1~beta", "1.0-1") == -1, "Tilde in release makes it a pre-release"
    assert rpmevrcmp("1.0~rc2-1", "1.0~rc1-1") == 1, "Comparing two pre-releases"
    assert rpmevrcmp("1.0^1-1", "1.0-1") == 1, "Caret in version makes it a post-release"
    assert rpmevrcmp("1.0-1^patch", "1.0-1") == 1, "Caret in release makes it a post-release"
    assert rpmevrcmp("1.0-1", "1.0.1") == -1, "Version '1.0' is older than '1.0.1', regardless of release"
    assert rpmevrcmp("1.0^1-1", "1.0~rc1-1") == 1, "Post-release (caret) is newer than pre-release (tilde)"
    assert rpmevrcmp("1.0-1^1", "1.0-1~rc1") == 1, "Post-release vs. pre-release in the release field"
    assert rpmevrcmp("1:1.0-1", "1.0-20") == 1, "Epoch comparison takes ultimate precedence"
    assert rpmevrcmp("1.0-^1", "1.0^1") == -1, "Hyphen splits V-R, so '1.0' is compared to '1.0^1'"
    assert rpmevrcmp("1.0.1-1", "1-0-1-1") == 1, "Dash in Release"
    assert rpmevrcmp("1.0.1-1", "1.0.1-1-1") == -1, "Dash in Release #2"
    assert rpmevrcmp("1.0^2~beta-1", "1.0^2-1") == -1, "Pre-release of a post-release is older"
    assert rpmevrcmp("foo:1.0-1", "1.0-1") == -1, "Non-numeric epoch 'foo' is treated like version"
    assert rpmevrcmp("foo:1.0-1", "bar:1.0-1") == 1, "Two different non-numeric epochs"
