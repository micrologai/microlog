#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import unittest

from microlog import log
from microlog.microlog import symbols

TEST_SYMBOL = 'microlog.is.cool'

class SymbolsTest(unittest.TestCase):
    def setUp(self):
        symbols.clear()
        log.clear()

    def test_index(self):
        self.assertEqual(log.empty(), True)
        index = indexSymbol(TEST_SYMBOL)
        self.assertEqual(index, 0)
        self.assertEqual(log.empty(), False)

    def test_put(self):
        self.assertEqual(log.empty(), True)
        symbols.put(25, TEST_SYMBOL)
        symbol = getSymbol(25)
        self.assertEqual(symbol, TEST_SYMBOL)
        self.assertEqual(log.empty(), True)

    def test_unmarshall(self):
        self.assertEqual(log.empty(), True)
        unmarshallSymbol([0, 13, TEST_SYMBOL])
        symbol = getSymbol(13)
        self.assertEqual(symbol, TEST_SYMBOL)
        self.assertEqual(log.empty(), True)


if __name__ == "__main__":
    unittest.main()
