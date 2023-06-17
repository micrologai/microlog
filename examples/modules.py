#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import sys
sys.path.insert(0, ".")
            
import microlog.api as api
import time

def loadModule(name):
    __import__(name)

def unmarshall(name, count):
    time.sleep(1)
    api.info(f"""
        Import: {name}
        Module count should increase by ~{count}.
        Notice the yellow line in the status bar.
    """)
    loadModule(name)

unmarshall("pytest", 175)
unmarshall("pandas", 430)
unmarshall("networkx", 280)