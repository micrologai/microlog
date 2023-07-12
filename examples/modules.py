#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import sys
sys.path.insert(0, ".")
            
import microlog.api as api
import time

def loadModule(name):
    __import__(name)


def delay(seconds):
    start = time.time()
    while time.time() - start < seconds:
        pass

def load(name, count):
    delay(1)
    api.info(f"""
        Import: {name}
        Module count should increase by ~{count}.
        Notice the yellow line in the status bar.
    """)
    loadModule(name)


load("pytest", 175)
load("pandas", 430)
load("networkx", 280)