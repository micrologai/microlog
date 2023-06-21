#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import json
import sys
import unittest
from unittest.mock import MagicMock
sys.modules["js"] = MagicMock()
sys.modules["pyodide"] = MagicMock()
from microlog import log
from dashboard.views.marker import MarkerView
from dashboard.canvas import Canvas

class TestMarkerView(unittest.TestCase):
    def setUp(self):
        log.log.load(json.dumps({
            "calls": [],
            "markers": [
                {
                    "when": 0.0015697440248914063,
                    "kind": 5,
                    "message": "test",
                    "stack": [
                        "microlog/api.py#23#  File \"microlog/api.py\", line 23, in test\n    pass",
                        "microlog/api.py#37#  File \"microlog/api.py\", line 37, in test\n    pass",
                    ],
                    "duration": 0.1
                },
            ],
            "statuses": [],
            "begin": 297246.842675386
        }))
        self.canvas = Canvas("", lambda: None)
        self.marker = MarkerView(self.canvas, log.log.markers[0])


    @unittest.mock.patch('dashboard.canvas.Canvas.image')
    @unittest.mock.patch('dashboard.canvas.Canvas.fromScreenDimension', return_value=10)
    def test_draw(self, mock_image, mock_fromscreendimension):
        self.assertEqual(len(log.log.markers), 1)
        self.marker.draw()
        self.assertTrue(mock_image.called)

    @unittest.mock.patch('dashboard.canvas.Canvas.toScreenDimension', return_value=10)
    @unittest.mock.patch('dashboard.canvas.Canvas.width', return_value=1000)
    def test_offscreen_negative(self, mock_toScreenDimension, mock_width):
        self.canvas.width = lambda: 1000
        self.marker.x = self.canvas.fromScreenX(-25)
        self.marker.w = self.canvas.fromScreenDimension(10)
        self.assertTrue(self.marker.offscreen())

    @unittest.mock.patch('dashboard.canvas.Canvas.toScreenDimension', return_value=10)
    @unittest.mock.patch('dashboard.canvas.Canvas.width', return_value=1000)
    def test_offscreen_positive(self, mock_toScreenDimension, mock_width):
        self.marker.x = self.canvas.fromScreenX(25)
        self.marker.w = self.canvas.fromScreenDimension(10)
        self.assertFalse(self.marker.offscreen())


if __name__ == "__main__":
    unittest.main() 
