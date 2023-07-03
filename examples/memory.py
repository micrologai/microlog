#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import sys
sys.path.insert(0, ".")

import gc
import time
import microlog

def showMemoryInfo():
    print(f"Number of live objects on the heap: {len(gc.get_objects()):,}")
    microlog.heap()


class MemoryLeak():
    def __init__(self):
        self.memory = f"{time.time()}" * 10000


def allocate1GB(run):
    memory = []
    for n in range(10000):
        memory.append(MemoryLeak())
    print("Allocating a thousand instances...")
    return memory


def takeShortPauze():
    time.sleep(0.2)


def allocateLotsOfMemory():
    memory = []
    for n in range(5):
        memory.append(allocate1GB(n))
        takeShortPauze()
    return memory


microlog.info("The process size warnings are added by microlog automatically.")

for n in range(3):
    showMemoryInfo()
    memory = allocateLotsOfMemory()
    del memory
    time.sleep(1)
showMemoryInfo()



