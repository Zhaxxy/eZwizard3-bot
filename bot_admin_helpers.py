import sys


def is_in_test_mode() -> bool:
    return '-t' in (x.casefold() for x in sys.argv[1:])


def is_in_fast_boot_mode() -> bool:
    return '-r' in (x.casefold() for x in sys.argv[1:])
