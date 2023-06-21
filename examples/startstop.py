#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
# A Microlog example that uses start and stop
# 

import microlog
import time


microlog.start("examples.startstop-1")
time.sleep(0.5)
microlog.stop()


with microlog.enabled("examples.startstop-2"):
    time.sleep(0.5)

