#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import json
import sys
import unittest
from unittest.mock import MagicMock

sys.modules["js"] = MagicMock()
sys.modules["pyodide"] = MagicMock()

import microlog
from dashboard.views.call import CallView
from microlog import log
from dashboard.canvas import Canvas
from dashboard import config



class TestCallView(unittest.TestCase):

    def setUp(self):
        microlog.stop()
        microlog.log.log.load(json.dumps({
            "calls": [
                {
                    "when": 0.0,
                    "threadId": 1,
                    "callSite": {
                        "filename": "test1.py",
                        "lineno": 1,
                        "name": "microlog.test.call"
                    },
                    "callerSite": {
                        "filename": "test2.py",
                        "lineno": 2,
                        "name": "microlog.test.caller"
                    },
                    "depth": 2,
                    "duration": 1.0
                },
                {
                    "when": 1.0,
                    "threadId": 1,
                    "callSite": {
                        "filename": "test1.py",
                        "lineno": 3,
                        "name": "microlog.test.call"
                    },
                    "callerSite": {
                        "filename": "test2.py",
                        "lineno": 4,
                        "name": "microlog.test.caller"
                    },
                    "depth": 2,
                    "duration": 1.0
                }
            ],
            "markers": [],
            "statuses": [],
            "begin": 297246.842675386
        }))

    def test_get_full_name(self):
        canvas = Canvas("", lambda: None)
        view = CallView(canvas, log.log.calls[0])
        self.assertEqual(view.getFullName(), "microlog.test.call")

    def test_get_short_name(self):
        canvas = Canvas("", lambda: None)
        view = CallView(canvas, log.log.calls[0])
        self.assertEqual(view.getShortName(), "call")

    @unittest.mock.patch('dashboard.canvas.Canvas._fillRect')
    def test_draw_first_call(self, mock_fillrect):
        CallView(Canvas("", lambda: None), log.log.calls[0]).draw("red", "green")
        offset = config.CANVAS_INITIAL_OFFSET_X
        mock_fillrect.assert_called_once_with(offset, 44, 100.0, 21, 'red')

    @unittest.mock.patch('dashboard.canvas.Canvas._fillRect')
    def test_draw_second_call(self, mock_fillrect):
        CallView(Canvas("", lambda: None), log.log.calls[1]).draw("red", "green")
        offset = config.CANVAS_INITIAL_OFFSET_X
        mock_fillrect.assert_called_once_with(100.0 + offset, 44, 100.0, 21, 'red')

    @unittest.mock.patch('dashboard.canvas.Canvas._fillRect')
    def test_draw_call_scaled(self, mock_fillrect):
        canvas = Canvas("", lambda: None)
        canvas.scaleX = 4.0
        CallView(canvas, log.log.calls[1]).draw("orange", "yellow")
        offset = config.CANVAS_INITIAL_OFFSET_X
        mock_fillrect.assert_called_once_with(4 * 100.0 + offset, 44, 4 * 100.0, 21, 'orange')


if __name__ == '__main__':
    unittest.main()
