#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import unittest

from microlog import log
from microlog.api import models

TEST_SYMBOL = 'microlog.is.cool'

class SymbolsTest(unittest.TestCase):
    def test_index(self):
        models.start()
        index = models.indexSymbol(TEST_SYMBOL)
        self.assertEqual(index, 0)
        models.start()

    def test_put(self):
        models.start()
        models.putSymbol(25, TEST_SYMBOL)
        symbol = models.getSymbol(25)
        self.assertEqual(symbol, TEST_SYMBOL)
        models.start()

    def test_unmarshall(self):
        models.start()
        models.unmarshallSymbol([0, 13, TEST_SYMBOL])
        symbol = models.getSymbol(13)
        self.assertEqual(symbol, TEST_SYMBOL)
        models.start()


if __name__ == "__main__":
    unittest.main()
