#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import time
import unittest

from microlog import log


class EventsTest(unittest.TestCase):
    def test_get(self):
        log.clear()
        event = [2, 0.072707, [0.0, 34359738368, 11985367040], [53.80656124099089], [143]]
        log.put(event)
        self.assertEqual(log.get(), event)

    def test_now(self):
        now1 = log.now()
        time.sleep(0.1)
        now2 = log.now()
        self.assertGreaterEqual(now2, now1)

    def test_clear(self):
        log.clear()
        self.assertEqual(log.count, 0)
        self.assertEqual(log.empty(), True)
        log.put(event=(8, 15, 29, 120, 31)),

    def test_put(self):
        log.clear()
        log.put(event=(8, 15, 29, 120, 31)),
        self.assertEqual(log.count, 1)
        self.assertEqual(log.empty(), False)

    def test_empty(self):
        self.assertEqual(log.empty(), False) # one event is always added
        log.clear()
        self.assertEqual(log.empty(), True)
        log.put(event=(8, 15, 29, 120, 31)),
        self.assertEqual(log.empty(), False)

if __name__ == "__main__":
    unittest.main()