#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import sys
import unittest
from unittest.mock import MagicMock

sys.modules["js"] = MagicMock()
sys.modules["pyodide"] = MagicMock()

from dashboard.canvas import Canvas
from dashboard import config


class TestCanvas(unittest.TestCase):

    def test_getScreenX(self):
        canvas = Canvas("", lambda: None)
        offset = config.CANVAS_INITIAL_OFFSET_X
        x = 0.1
        self.assertEqual(canvas.toScreenX(x), offset + x)

    def test_getScreenXAtScale(self):
        canvas = Canvas("", lambda: None)
        offset = config.CANVAS_INITIAL_OFFSET_X
        x = 0.1
        canvas.scaleX = 0.5
        self.assertEqual(canvas.toScreenX(x), offset + x / 2)
        canvas.scaleX = 4.0
        self.assertEqual(canvas.toScreenX(x), offset + x * 4)

    def test_getScreenDimension(self):
        canvas = Canvas("", lambda: None)
        w = 100.1
        self.assertEqual(canvas.toScreenDimension(w), w)

    def test_getScreenDimensionAtScale(self):
        canvas = Canvas("", lambda: None)
        w = 100.1
        canvas.scaleX = 0.5
        self.assertEqual(canvas.toScreenDimension(w), w / 2)
        canvas.scaleX = 4.0
        self.assertEqual(canvas.toScreenDimension(w), 4 * w)


if __name__ == '__main__':
    unittest.main()

