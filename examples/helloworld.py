#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
# The simplest Microlog example just prints something.
# 

import logging
import sys
import time

#
# Create a logger
#
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


#
# Create a function that logs and prints something and then sleeps a bit
#
def sayHello():
    # generate a debug log entry, this will show in Microlog as a bug icon
    logger.debug("Saying hello")  

    # generate a info log entry, this will show in Microlog as a information icon
    logger.info("Saying hello")  

    # generate a warning log entry, this will show in Microlog as a warning sign icon
    logger.warning("Saying hello")  

    # generate a error log entry, this will show in Microlog as a stop sign icon
    logger.error("Saying hello")  

    # print statements gets saved as a microlog "info" event, with a stacktrace
    print("hello world") 
    time.sleep(0.5)


#
# Call the sayHello function a few times
#
for n in range(3):
    # print statements to stderr get saved as a microlog "error" event, with a stacktrace
    print("Run", n, file=sys.stderr)
    sayHello()
    time.sleep(0.5)
    print()

#
# Notice we have no calls to microlog anywhere in this example.
#
# Microlog automatically captures the following:
#  - Statistics, such as memory usage, number of modules, and CPU
#  - Execution profile by sampling the Python code as it runs
#  - Print and logging statements
#
# During setup, microlog was added to sitecustomize.py, so it runs
# as an agent for all executions of the python interpreter.
#
import os
import site
import sys

sitepackages = site.getsitepackages()[0]
sys.path.append(sitepackages)
print("Microlog is enabled globally for", sys.executable, "in:")
print(os.path.join(sitepackages, "sitecustomize.py"))
print()
