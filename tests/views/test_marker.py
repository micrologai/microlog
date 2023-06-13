#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import unittest
from unittest.mock import MagicMock

class TestMarkerView(unittest.TestCase):
    def setUp(self):
        import sys
        sys.modules["js"] = MagicMock()
        sys.modules["pyodide"] = MagicMock()

        from dashboard.views import marker
        from dashboard import canvas
        from microlog import info
        from microlog import warn
        from microlog import error
        from microlog import debug
        from microlog import config
        from microlog import log
        log.buffer = [
            (0, 19, 'Hello'), # Symbol
            (0, 26, 'unittest/case.py#587#  File \\"unittest/case.py\\", line 587, in run\\n    self._callSetUp()'), # Symbol
            (0, 27, 'unittest/case.py#546#  File \\"unittest/case.py\\", line 546, in _callSetUp\\n    self.setUp()'), # Symbol
            (0, 28, 'micrologai/microlog/tests/views/test_marker.py#21#  File \\"micrologai/microlog/tests/views/test_marker.py\\", line 21, in setUp\\n    info(\\"Hello\\")'), # Symbol
            [3, 0.05523181900207419, 19, [26, 27, 28]], # Info
        ]
        event = log.buffer[-1]
        log.validate()
        self.canvas = canvas.Canvas("", lambda: None)
        self.marker = marker.MarkerView(self.canvas, event)

    @unittest.mock.patch('dashboard.canvas.Canvas.image')
    def test_draw(self, mock_image):
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
