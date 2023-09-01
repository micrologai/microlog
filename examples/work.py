#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import microlog
import random
import time

def do_work_1():
    start = time.time()
    import pandas
    duration = time.time() - start
    if duration > 0.1:
        print(f"import of pandas took {duration:.2}s")
    return [ [random.random() for col in range(50)] for row in range(250) ]

def do_work_2():
    return [ [random.random() for col in range(50)] for row in range(250) ]

def do_work_3():
    return [ [random.random() for col in range(50)] for row in range(250) ]

def main():
    with microlog.enabled("work-work-work"):
        start = time.time()
        while time.time() - start < 5:
            do_work_1()
            do_work_2()
            do_work_3()
        
main()
