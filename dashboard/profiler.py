#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from collections import defaultdict
import datetime
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
            try:
                profiler.profileCount.clear()
                profiler.profileTime.clear()
                return function(*args, **argv)
            finally:
                if enabled:
                    generateReport(explanation)
        return inner
    return decorator
       
    
def generateReport(explanation):
    print("-" * 55)
    print(explanation)
    print("Recorded at:", datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    print("-" * 55)
    print("Operation                       Calls    Time")
    print("-" * 55)
    for key in profiler.profileCount:
        count = profiler.profileCount[key]
        total = profiler.profileTime[key]
        print(f"{key:30s} {count:6d} {total:6.3f}s")
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