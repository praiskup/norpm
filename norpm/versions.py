"""
Compare Versions, and EVRs
"""


def rpmvercmp(a, b):
    """
    A Python implementation of rpm/rpmio/rpmverrcmp.cc.
    """

    # Easy comparison to see if versions are identical
    if a == b:
        return 0

    i, j = 0, 0
    len_a, len_b = len(a), len(b)

    # loop through each version segment and compare them
    while i < len_a or j < len_b:
        # Skip any non-alphanumeric characters, but not '~' or '^'.
        while i < len_a and not a[i].isalnum() and a[i] not in '~^':
            i += 1
        while j < len_b and not b[j].isalnum() and b[j] not in '~^':
            j += 1

        # Handle the tilde separator, it sorts before everything else
        is_tilde_a = i < len_a and a[i] == '~'
        is_tilde_b = j < len_b and b[j] == '~'
        if is_tilde_a or is_tilde_b:
            if not is_tilde_b:
                return -1
            if not is_tilde_a:
                return 1
            i += 1
            j += 1
            continue

        # Handle the caret separator, it sorts after everything else
        is_caret_a = i < len_a and a[i] == '^'
        is_caret_b = j < len_b and b[j] == '^'
        if is_caret_a or is_caret_b:
            if i >= len_a:
                return -1
            if j >= len_b:
                return 1
            if not is_caret_b:
                return -1
            if not is_caret_a:
                return 1
            i += 1
            j += 1
            continue

        # If we ran to the end of either, we are finished with the loop
        if i >= len_a or j >= len_b:
            break

        start_a, start_b = i, j

        # Grab first completely alpha or completely numeric segment
        is_digit = a[i].isdigit()
        if is_digit:
            while i < len_a and a[i].isdigit():
                i += 1
            while j < len_b and b[j].isdigit():
                j += 1
        else:
            while i < len_a and a[i].isalpha():
                i += 1
            while j < len_b and b[j].isalpha():
                j += 1

        seg_a = a[start_a:i]
        seg_b = b[start_b:j]

        # Handle case where segments are different types (numeric vs alpha)
        if not seg_b:
            if is_digit:
                return 1  # Numeric is newer than alpha
            return -1

        if is_digit:
            # Overflow-safe numeric comparison
            seg_a = seg_a.lstrip('0')
            seg_b = seg_b.lstrip('0')

            len_seg_a, len_seg_b = len(seg_a), len(seg_b)
            if len_seg_a > len_seg_b:
                return 1
            if len_seg_b > len_seg_a:
                return -1

        # If lengths are equal (or for alpha), lexicographical comparison is sufficient
        if seg_a != seg_b:
            if seg_a > seg_b:
                return 1
            return -1

    # After loop, handle cases where one version string is a prefix of the other,
    # or if they are logically equal (like '1.05' and '1.5').
    if i >= len_a and j >= len_b:
        return 0

    if i >= len_a:
        return -1

    return 1


def _parse_rpm_evr(version_string):
    """
    Split string into three parts EPOCH:Version-Release.  Epoch and Release are
    optional (if unspecified, None is returned).
    """
    epoch = None
    rest = version_string
    if ':' in version_string:
        epoch, rest = version_string.split(':', 1)
    version = rest
    release = None
    if '-' in rest:
        version, release = rest.split('-', 1)

    return epoch, version, release


def rpmevrcmp(a, b):
    """
    Compare EVRs, e.g. "1:0.2-3"
    """
    epoch_a, version_a, release_a = _parse_rpm_evr(a)
    epoch_b, version_b, release_b = _parse_rpm_evr(b)
    if epoch_a is None:
        epoch_a = "0"
    if epoch_b is None:
        epoch_b = "0"
    if epoch_diff := rpmvercmp(epoch_a, epoch_b):
        return epoch_diff
    if version_diff := rpmvercmp(version_a, version_b):
        return version_diff
    if release_a or release_b:
        if release_a and release_b:
            return rpmvercmp(release_a, release_b)
        if release_a:
            return 1
        return -1
    return 0
