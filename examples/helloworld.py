#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
# The simplest Microlog example just prints something.
# 
# During setup, microlog was added to sitecustomize.py, so it runs
# as an agent for all executions of the python interpreter.
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
    logger.debug("Saying hello")  
    logger.info("Saying hello")  
    logger.warning("Saying hello")  
    logger.error("Saying hello")  
    print("hello world") # this gets saved as a microlog event, with a stacktrace
    time.sleep(0.5)


#
# Call the sayHello function a few times
#
for n in range(3):
    import microlog
    sayHello()
    time.sleep(0.5)
    print("Run", n, file=sys.stderr)

#
# Notice we have no calls to microlog anywhere in this example.
#
# Microlog automatically captures the following:
#  - Statistics, such as memory usage, number of modules, and CPU
#  - Execution profile by sampling the Python code as it runs
#  - Print and logging statements
#
