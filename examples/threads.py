#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
# Run a program with multiple threads.
# 

import time
import threading


def sleep(n):
    time.sleep(n)


def run(n):
    sleep(n)
    thread = threading.current_thread()
    thread.name = f"Thread {n} - {thread.ident}"
    print("run thread", n, thread)
    sleep(n)


#
# Start a few threads and run them
#
threads = [
    threading.Thread(target=lambda: run(1)),
    threading.Thread(target=lambda: run(2)),
    threading.Thread(target=lambda: run(3)),
]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()
time.sleep(2)
