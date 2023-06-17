#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import unittest

from microlog import log
from microlog.api import models

TEST_SYMBOL = 'microlog.is.cool'

class SymbolsTest(unittest.TestCase):
    def test_index(self):
        models.clear()
        index = models.indexSymbol(TEST_SYMBOL)
        self.assertEqual(index, 0)
        models.clear()

    def test_put(self):
        models.clear()
        models.putSymbol(25, TEST_SYMBOL)
        symbol = models.getSymbol(25)
        self.assertEqual(symbol, TEST_SYMBOL)
        models.clear()

    def test_unmarshall(self):
        models.clear()
        models.unmarshallSymbol([0, 13, TEST_SYMBOL])
        symbol = models.getSymbol(13)
        self.assertEqual(symbol, TEST_SYMBOL)
        models.clear()


if __name__ == "__main__":
    unittest.main()
