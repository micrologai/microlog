#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
# A Microlog example that uses start and stop
# 

import microlog
import time


microlog.start("startstop example - part 1")
time.sleep(0.5)
microlog.stop()


with microlog.enabled("startstop example - part 2"):
    time.sleep(0.5)

