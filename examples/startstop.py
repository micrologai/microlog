#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
# A Microlog example that uses start and stop
# 

import microlog
import time

#
# Microlog can be enabled/disabled using start/stop calls.
#
microlog.start("examples.startstop-1")

print("this statement is recorded by Microlog in log 1")
time.sleep(0.5) # code in here is being recorded

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
    print("this statement is recorded by Microlog in log 2")
    time.sleep(0.5) 


print("This statement is not recorded by Microlog")