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


    def test_clear(self):
        log.clear()
        self.assertEqual(len(log.buffer), 0)
        log.put(event=(8, 15, 29, 120, 31)),

    def test_put(self):
        log.clear()
        log.put(event=(8, 15, 29, 120, 31)),
        self.assertEqual(len(log.buffer), 1)


if __name__ == "__main__":
    unittest.main()