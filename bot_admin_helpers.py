import sys

_GLOBAL_MUTABLE_IN_TEST_MODE: None | bool = None

def toggle_test_mode_bool() -> bool:
    global _GLOBAL_MUTABLE_IN_TEST_MODE
    if _GLOBAL_MUTABLE_IN_TEST_MODE is None:
        _GLOBAL_MUTABLE_IN_TEST_MODE = True
    else:
        _GLOBAL_MUTABLE_IN_TEST_MODE = not _GLOBAL_MUTABLE_IN_TEST_MODE
     
    return _GLOBAL_MUTABLE_IN_TEST_MODE


def is_in_test_mode() -> bool:
    global _GLOBAL_MUTABLE_IN_TEST_MODE
    
    if _GLOBAL_MUTABLE_IN_TEST_MODE is not None:
        return _GLOBAL_MUTABLE_IN_TEST_MODE
    return '-t' in (x.casefold() for x in sys.argv[1:])


def is_in_fast_boot_mode() -> bool:
    return '-r' in (x.casefold() for x in sys.argv[1:])
