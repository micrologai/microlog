#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from collections import defaultdict
import time

enabled = True

class Profiler():
    def __init__(self):
        self.profileCount = defaultdict(int)
        self.profileTime = defaultdict(float)

profiler = Profiler()
    

def report(explanation):
    def decorator(function):
        def inner(*args, **argv):
            start = time.perf_counter()
            try:
                profiler.profileCount.clear()
                profiler.profileTime.clear()
                return function(*args, **argv)
            finally:
                if enabled:
                    generateReport(explanation, time.perf_counter() - start)
        return inner
    return decorator
       
    
def generateReport(explanation, duration):
    print("-" * 55)
    print(explanation, f"{duration:.3}s")
    print("-" * 55)
    print("Operation                       Calls  Time")
    print("-" * 55)
    results = sorted([
        (key, profiler.profileCount[key], profiler.profileTime[key])
        for key in profiler.profileCount
    ], key=lambda item: -item[-1])
    for key, count, duration in results:
        print(f"{key:30s} {count:6d} {duration:6.3f}s")
    print("-" * 55)


def profile(name):
    def decorator(function):
        def inner(*args, **argv):
            try:
                if enabled:
                    start = time.time()
                return function(*args, **argv)
            finally:
                if enabled:
                    profiler.profileCount[name] += 1
                    profiler.profileTime[name] += time.time() - start
        return inner
    return decorator


def getCount(key):
    return profiler.profileCounts[key]


def getTime(key):
    return profiler.profileTime[key]