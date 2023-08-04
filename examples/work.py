#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import microlog
import random
import time

def do_work():
    start = time.time()
    while time.time() - start < 0.1:
        _ = [ [random.random() for col in range(100)] for row in range(100) ]

def do_work_1():
    do_work()

def do_work_2():
    do_work()

def do_work_3():
    do_work()


with microlog.enabled("work-work-work"):
    for n in range(10):
        do_work_1()
        do_work_2()
        do_work_3()