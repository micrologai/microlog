#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import time
import unittest

from microlog import log


class EventsTest(unittest.TestCase):
    def test_now(self):
        now1 = log.log.now()
        time.sleep(0.1)
        now2 = log.log.now()
        self.assertGreaterEqual(now2, now1)
