"""
Call getopt() directly.  The Python variant doesn't support
the %foo(:-:) syntax.
"""

import os
import ctypes

# Load libc
libc = ctypes.CDLL("libc.so.6")

def suppress_stderr(func, *args):
    """ avoid stderr polluting by glibc's getopt """
    original_stderr_fd = os.dup(2)
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull_fd, 2)
    os.close(devnull_fd)
    try:
        return func(*args)
    finally:
        os.dup2(original_stderr_fd, 2)
        os.close(original_stderr_fd)

def getopt(params, optstring):
    """
    Call getops directly from Glibc
    """
    libc.getopt.argtypes = [ctypes.c_int,
                            ctypes.POINTER(ctypes.c_char_p),
                            ctypes.c_char_p]
    libc.getopt.restype = ctypes.c_int

    argv = [b"norpm-macro-parser"] + [s.encode() for s in params]
    argc = len(argv)

    argv_array = (ctypes.c_char_p * argc)(*argv)

    optstring = optstring.encode()

    optarg = ctypes.c_char_p.in_dll(libc, "optarg")
    optind = ctypes.c_int.in_dll(libc, "optind")
    optind.value = 0
    optarg.value = None

    output = []

    while True:
        opt = suppress_stderr(libc.getopt, argc, argv_array, optstring)
        if opt == -1:
            break

        if opt == 1:
            break

        opt = "-" + chr(opt)

        if optarg.value is None:
            output.append((opt, ""))
            continue

        output.append((opt, optarg.value.decode() if optarg.value else ""))

    args = []
    for i in range(optind.value, argc):
        args.append(argv_array[i].decode())

    return output, args
