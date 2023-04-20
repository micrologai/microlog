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
    time.sleep(0.1)


def allocateLotsOfMemory():
    memory = []
    for n in range(5):
        memory.append(allocate1GB(n))
        takeShortPauze()
        showMemoryInfo()
    return memory


with microlog.enabled("Memory", 1.1, "Debug memory usage", traceDelay=0.005, verbose=True, showInBrowser=True):
    microlog.info("Microlog tracks memory.\n\nSee the red line growing in the status bar.")

    showMemoryInfo()
    memory = allocateLotsOfMemory()
    del memory
    for n in range(3):
        showMemoryInfo()
        time.sleep(1)

    microlog.info("The warning icons are added by microlog automatically.")

