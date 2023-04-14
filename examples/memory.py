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


@microlog.trace
def allocate1GB(run):
    memory = []
    for n in range(10000):
        memory.append(MemoryLeak())
    print("Allocating a thousand instances...")
    return memory


@microlog.trace
def allocateLotsOfMemory():
    memory = []
    for n in range(5):
        memory.append(allocate1GB(n))
        time.sleep(0.1)
        showMemoryInfo()
    return memory


with microlog.enabled("Memory", 1.1, "Debug memory usage", verbose=True, showInBrowser=True):
    microlog.info("Microlog tracks memory.\n\nSee the red line growing in the status bar.")

    showMemoryInfo()
    memory = allocateLotsOfMemory()
    del memory
    time.sleep(1)
    showMemoryInfo()

    microlog.info("The warning icons are added by microlog automatically.")

