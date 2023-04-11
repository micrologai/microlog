#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import time
import unittest

from microlog import events


class EventsTest(unittest.TestCase):
    def test_get(self):
        events.clear()
        event = [2, 0.072707, [0.0, 34359738368, 11985367040], [53.80656124099089], [143]]
        events.put(event)
        self.assertEqual(events.get(), event)

    def test_now(self):
        now1 = events.now()
        time.sleep(0.1)
        now2 = events.now()
        self.assertGreaterEqual(now2, now1)

    def test_clear(self):
        events.clear()
        self.assertEqual(events.count, 0)
        self.assertEqual(events.empty(), True)
        events.put(event=(8, 15, 29, 120, 31)),

    def test_put(self):
        events.clear()
        events.put(event=(8, 15, 29, 120, 31)),
        self.assertEqual(events.count, 1)
        self.assertEqual(events.empty(), False)

    def test_empty(self):
        self.assertEqual(events.empty(), False) # one event is always added
        events.clear()
        self.assertEqual(events.empty(), True)
        events.put(event=(8, 15, 29, 120, 31)),
        self.assertEqual(events.empty(), False)

if __name__ == "__main__":
    unittest.main()