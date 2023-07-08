#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import sys
sys.path.insert(0, ".")

from collections import Counter
import gc
import time
import microlog

def showMemoryInfo():
    top10 = "\n".join(
        f"- {name}: {count:,}"
        for name, count in Counter(type(obj).__name__ for obj in gc.get_objects()).most_common(10)
    )
    print(f"# Python Heap Details\n\nThe top ten of {len(gc.get_objects()):,} live objects:\n{top10}")


class MemoryLeak():
    def __init__(self):
        self.memory = f"{time.time()}" * 10000


def allocate1GB(run):
    takeShortPauze()
    return [MemoryLeak() for n in range(10000)]


def takeShortPauze():
    time.sleep(0.2)


def takeLongPause():
    time.sleep(1.5)


def allocateLotsOfMemory():
    return [allocate1GB(n) for n in range(5)]


def main():
    microlog.info("The process size warnings are added by microlog automatically.")

    showMemoryInfo()
    takeLongPause()

    for n in range(3):
        allocateLotsOfMemory()
        takeLongPause()
        gc.collect()
        showMemoryInfo()

    gc.collect()
    showMemoryInfo()


main()