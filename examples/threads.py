#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
# Run a program with multiple threads.
# 

import time
import random
import threading
import microlog
import pandas as pd


def work(n):
    work1(n)


def work1(n):
    work2(n)
        

@microlog.trace
def work2(n):
    time.sleep(random.random() * 3)
    print("run", n, threading.current_thread().ident)
    df = pd.DataFrame()
    for col in range(1000):
        df[col] = [col * 2]


def run():
    for n in range(5):
        work(n)


#
# Start a few threads and run them
#
threads = [threading.Thread(target=run) for n in range(3)]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()
