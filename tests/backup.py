"""
These were generated for the development/testing, and aren't used.
"""

import subprocess


def rpmevrcmp(ver1: str, ver2: str) -> int:
    """
    Call rpmvdev-vercmp on EVRs.
    """
    result = subprocess.run(
        ['rpmdev-vercmp', ver1, ver2],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False  # We handle the return code manually
    )

    if result.returncode == 0:
        return 0  # Versions are equal
    if result.returncode == 11:
        return 1  # ver1 is newer
    if result.returncode == 12:
        return -1 # ver1 is older
    # Raise an error for any other unexpected exit code.
    raise ValueError(
        f"rpmdev-vercmp returned an unexpected exit code: {result.returncode}"
    )


def rpmvercmp(ver1: str, ver2: str) -> int:
    """
    Call rpmvdev-vercmp for Versions only.
    """
    result = subprocess.run(
        ['rpmdev-vercmp', "0", ver1, "0", "0", ver2, "0"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False  # We handle the return code manually
    )

    if result.returncode == 0:
        return 0  # Versions are equal
    if result.returncode == 11:
        return 1  # ver1 is newer
    if result.returncode == 12:
        return -1 # ver1 is older
    # Raise an error for any other unexpected exit code.
    raise ValueError(
        f"rpmdev-vercmp returned an unexpected exit code: {result.returncode}"
    )
