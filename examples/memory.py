"""Example script that allocates memory and shows memory usage details."""

from collections import Counter
import gc
import time

start_counter = Counter(type(obj).__name__ for obj in gc.get_objects())

def show_memory_info():
    """Show memory usage details."""
    top10 = "\n".join(
        f"- {count} objects of type \"{name}\", which is " \
            f"{count - start_counter[name]:+,} since the start"
        for name, count in Counter(type(obj).__name__ for obj in gc.get_objects()).most_common(10)
    )
    print("# Python Heap Details")
    print(f"The top ten of {len(gc.get_objects()):,} live objects:")
    print(top10)


class MemoryLeak():
    """Class that simulates a memory leak by holding a large string."""
    def __init__(self):
        self.memory = f"{time.time()}" * 10000

def allocate_a_gigabyte():
    """Allocate approximately 1GB of memory."""
    take_short_pauze()
    show_memory_info()
    return [MemoryLeak() for _ in range(10000)]


def take_short_pauze():
    """Take a short pause to allow memory monitoring to catch up."""
    time.sleep(0.2)


def take_long_pauze():
    """Take a long pause to allow memory monitoring to catch up."""
    time.sleep(1.5)


def allocate_lots_of_memory():
    """Allocate lots of memory in a loop."""
    return [allocate_a_gigabyte() for _ in range(5)]


def main():
    """Main function to demonstrate memory allocation and monitoring."""

    print("The process size warnings are added by microlog automatically.")

    show_memory_info()
    take_long_pauze()

    for _ in range(3):
        allocate_lots_of_memory()
        take_long_pauze()
        gc.collect()
        show_memory_info()

    gc.collect()
    show_memory_info()


forced_leak = MemoryLeak()

main()
