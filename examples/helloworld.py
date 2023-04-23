#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
# The simplest Microlog example just prints something.
# 
# During setup, microlog was added to sitecustomize.py, so it runs
# as an agent for all executions of the python interpreter.
#

import time

def sayHello():
    print("hello world")
    time.sleep(0.1)

#
# Now call the sayHello function a few times
#
for n in range(10):
    sayHello()
    time.sleep(0.1)

#
# Notice we have no calls to microlog anywhere in this example.
# The logs are automatically captured.
#