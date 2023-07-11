#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import time

path = __file__


def leak_file_descriptor():
    open(path)
    print("Leaking a file descriptor:")
    print(" - File opened:", path)
    print(" - Microlog detects files that are opened, but never closed.")
    print(" - They are listed as a warning in the statusbar, at the end of the Timeline.")
    print()


def use_close():
    open(path).close()
    print("Using close:")
    print(" - File opened and closed:", path)
    print(" - This does not leak a file descriptor, so no warning is generated.")
    print()


def use_context_manager():
    print("Using a context manager:")
    with open(path) as io:
        print(" - File opened:", path)
        print(" - Files that are opened with a context manager are always safe.")
        print(" - The file descriptor will be released automatically.")
        print()


leak_file_descriptor()
time.sleep(2)
use_close()
time.sleep(2)
use_context_manager()
