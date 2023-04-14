import microlog

from collections import defaultdict
import gc
import time
import tracemalloc

KB = 1024
MB = KB * KB
GB = MB * KB


def toGB(amount):
    if amount / GB > 1: return f"{amount / GB:.1f}GB"
    if amount / MB > 1: return f"{amount / MB:.1f}MB"
    if amount / KB > 1: return f"{amount / KB:.1f}KB"
    return f"{amount} bytes"


class Memory():
    def __init__(self):
        self.previous = None
        self.hpy = None
        tracemalloc.start()

    def sample(self):
        import guppy
        import psutil

        if not self.hpy:
            self.hpy = guppy.hpy()
        sample = self.hpy.heap()
        diff = (sample - self.previous) if self.previous else "None"

        microlog.debug(f"""
            # Python memory analysis 
            
            System memory total: {toGB(psutil.virtual_memory().total)}<br>
            System memory used: {toGB(psutil.virtual_memory().used)}<br>
            Process memory size: {toGB(psutil.Process().memory_info().rss)}<br>
            Heap Size: {toGB(sample.size)}
            
            ## Current heap snapshot
            ```
            {sample.byrcs}
            ```

            ## Difference with previous snapshot
            ```
            {diff}
            ```
        """)
        self.previous = sample

    def stop(self):
        gc.collect()
        objects = gc.get_objects()
        objectsByType = defaultdict(int)
        for obj in objects:
            objectsByType[obj.__class__.__name__] += 1
        lines = [
            f"GC ran for {sum(gc.get_count())} times.",
            "",
            f"# The top ten {len(objects):,} live objects:",
        ]
        for clazz, count in list(sorted(objectsByType.items(), key=lambda item: -item[1])[:10]):
            lines.append(f"  - {clazz}: {count} instances")

        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics('lineno')
        lines.append("# The top ten memory allocators:")
        for stat in top_stats[:10]:
            lines.append(f"  - {stat}")
        microlog.info("<br>\n".join(lines))

memory = Memory()

def heap():
    memory.sample()

def stop():
    memory.stop()