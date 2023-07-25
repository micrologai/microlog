#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
# A Microlog example that uses start and stop
# 

import microlog
import time


time.sleep(0.5)
print("This code is recorded when Microlog is set up in sitecustomize.py")
time.sleep(0.5)

#
# Microlog can be enabled/disabled using start/stop calls.
#
microlog.start("examples.startstop-1")

time.sleep(0.5)
print("This code is recorded by Microlog in startstop-1")
time.sleep(0.5)

microlog.stop()

#
# Microlog is re-entrant and allows multiple start/stop sessions.
# Logs are only generated when Microlog is enabled.
#
print("This statement is not recorded by Microlog")


#
# A new session can be created using a context manager. 
#
with microlog.enabled("examples.startstop-2"):
    time.sleep(0.5)
    print("This code is recorded by Microlog in startstop-2")
    time.sleep(0.5) 


print("This statement is not recorded by Microlog")