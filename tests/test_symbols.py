#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import unittest

from microlog import events
from microlog import symbols

TEST_SYMBOL = 'microlog.is.cool'

class SymbolsTest(unittest.TestCase):
    def setUp(self):
        symbols.clear()
        events.clear()

    def test_index(self):
        self.assertEqual(events.empty(), True)
        index = symbols.index(TEST_SYMBOL)
        self.assertEqual(index, 0)
        self.assertEqual(events.empty(), False)

    def test_put(self):
        self.assertEqual(events.empty(), True)
        symbols.put(25, TEST_SYMBOL)
        symbol = symbols.get(25)
        self.assertEqual(symbol, TEST_SYMBOL)
        self.assertEqual(events.empty(), True)

    def test_load(self):
        self.assertEqual(events.empty(), True)
        symbols.load([0, 13, TEST_SYMBOL])
        symbol = symbols.get(13)
        self.assertEqual(symbol, TEST_SYMBOL)
        self.assertEqual(events.empty(), True)


if __name__ == "__main__":
    unittest.main()
