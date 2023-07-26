#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import os
import sys
import unittest
from unittest.mock import MagicMock
sys.modules["js"] = MagicMock()
sys.modules["pyodide"] = MagicMock()
from microlog import log
from dashboard.views.marker import MarkerView
from dashboard.canvas import Canvas

LOG = open(os.path.join(os.path.dirname(__file__), "helloworld.log")).read()

class TestMarkerView(unittest.TestCase):
    def setUp(self):
        log.log.load(LOG)
        self.canvas = Canvas("", lambda: None)
        self.marker = MarkerView(self.canvas, log.log.markers[0])


    @unittest.mock.patch('dashboard.canvas.Canvas.image')
    @unittest.mock.patch('dashboard.canvas.Canvas.fromScreenDimension', return_value=10)
    def test_draw(self, mock_image, mock_fromscreendimension):
        self.assertEqual(len(log.log.markers), 25)
        self.marker.draw()
        self.assertTrue(mock_image.called)

    @unittest.mock.patch('dashboard.canvas.Canvas.toScreenDimension', return_value=10)
    @unittest.mock.patch('dashboard.canvas.Canvas.width', return_value=1000)
    def test_offscreen_negative(self, mock_toScreenDimension, mock_width):
        self.canvas.offsetX = -100
        self.assertTrue(self.marker.offscreen(self.canvas.scaleX, self.canvas.offsetX, self.canvas.width()))

    @unittest.mock.patch('dashboard.canvas.Canvas.toScreenDimension', return_value=10)
    @unittest.mock.patch('dashboard.canvas.Canvas.width', return_value=1000)
    def test_offscreen_positive(self, mock_toScreenDimension, mock_width):
        self.canvas.offsetX = 2000
        self.assertTrue(self.marker.offscreen(self.canvas.scaleX, self.canvas.offsetX, self.canvas.width()))


if __name__ == "__main__":
    unittest.main() 
