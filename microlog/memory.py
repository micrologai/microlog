import microlog

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
        pass


memory = Memory()

def heap():
    memory.sample()

def stop():
    memory.stop()