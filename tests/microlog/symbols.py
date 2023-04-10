#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from mock import patch
import unittest

from microlog import events
from microlog import symbols

TEST_SYMBOL = 'microlog.is.cool'

class SymbolsTest(unittest.TestCase):

    def test_index(self):
        events.clear()
        self.assertEqual(events.empty(), True)
        index = symbols.index(TEST_SYMBOL)
        self.assertEqual(index, 0)
        self.assertEqual(events.empty(), False)

    def test_put(self):
        symbols.put(25, TEST_SYMBOL)
        symbol = symbols.get(25)
        self.assertEqual(symbol, TEST_SYMBOL)
        self.assertEqual(events.empty(), False)

    def test_load(self):
        symbols.load([0, 13, TEST_SYMBOL])
        symbol = symbols.get(13)
        self.assertEqual(symbol, TEST_SYMBOL)
        self.assertEqual(events.empty(), False)


if __name__ == "__main__":
    unittest.main()
