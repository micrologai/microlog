#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import collections
import os
import time

EVENT_KIND_SYMBOL = 0
EVENT_KIND_CALL = 1
EVENT_KIND_STATUS = 2
EVENT_KIND_INFO = 3
EVENT_KIND_WARN = 4
EVENT_KIND_DEBUG = 5
EVENT_KIND_ERROR = 6
EVENT_KIND_CALLSITE = 7
EVENT_KIND_META = 8

kinds = [
    "Symbol",
    "Call",
    "Status",
    "Info",
    "Warn",
    "Debug",
    "Error",
    "Callsite",
    "Meta",
]

totalOverhead = 0
totalBackgroundOverhead = collections.defaultdict(float)
totalLogEventCount = 0
totalPostProcessing = 0
outputFilename = ""
zipFilename = ""
outputUrl = ""

start = time.time()

def micrologAPI(function):
    def micrologAPIWrapper(*args, **argv):
        global totalOverhead
        start = time.time()
        try:
            return function(*args, **argv)
        finally:
            end = time.time()
            totalOverhead += end - start
    return micrologAPIWrapper


def memoize(function):
    memo = {}
    def helper(x):
        if x not in memo:            
            memo[x] = function(x)
        return memo[x]
    return helper


def statistics():
    end = time.time()
    lines = []
    lines.append("-" * 80)
    lines.append("Microlog Statistics:")
    lines.append("-" * 80)
    lines.append(f"-  number of events            {totalLogEventCount:,}")
    lines.append(f"-  file size                   {os.stat(outputFilename).st_size:,} bytes")
    lines.append(f"-  compressed size             {os.stat(zipFilename).st_size:,} bytes")
    lines.append(f"-  overhead for microlog       {totalOverhead:.3f}s")
    for name, total in totalBackgroundOverhead.items():
        lines.append(f"   - {name:24s}  {total:.3f}s")
    lines.append(f"   - post-processing           {totalPostProcessing:.3f}s")
    lines.append(f"-  uncompressed output file    {outputFilename}")
    lines.append(f"-  browser URL                 {outputUrl}")
    lines.append(f"-  wall time                   {end-start:.3f}s")
    lines.append(f"-  total microlog overhead     {(totalOverhead + totalPostProcessing) * 100 / (end-start):.2f}%")
    lines.append("-" * 80)
    return "\n".join(lines)
