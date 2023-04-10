#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import time
import queue

count = 0
begin = time.perf_counter()
eventQueue = queue.Queue()

def now():
    return time.perf_counter() - begin

def put(event):
    global count
    count += 1
    eventQueue.put(event)
            
def clear():
    global eventQueue, count
    eventQueue = queue.Queue()
    count = 0
            
def get():
    return eventQueue.get()

def empty():
    return eventQueue.empty()