#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import os
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

LOG = open(os.path.join(os.path.dirname(__file__), "helloworld.log")).read()


class TestCallView(unittest.TestCase):

    def setUp(self):
        microlog.stop()
        microlog.log.log.load(LOG)

    def test_get_full_name(self):
        canvas = Canvas("", lambda: None)
        view = CallView(canvas, log.log.calls[0])
        self.assertEqual(view.getFullName(), "logging.Logger.debug")

    def test_get_short_name(self):
        canvas = Canvas("", lambda: None)
        view = CallView(canvas, log.log.calls[0])
        self.assertEqual(view.getShortName(), "debug")

    @unittest.mock.patch('dashboard.canvas.Canvas._fillRect')
    def test_draw_first_call(self, mock_fillrect):
        for call in log.log.calls:
            if call.callSite.name.endswith("sayHello"):
                view = CallView(Canvas("", lambda: None), call)
                view.draw("red", "green")
                mock_fillrect.assert_called_once_with(49, 22, 42, 21, 'red')
                return
        raise ValueError("Could not find sayHello")

    @unittest.mock.patch('dashboard.canvas.Canvas._fillRect')
    def test_draw_call_scaled(self, mock_fillrect):
        for call in log.log.calls:
            if call.callSite.name.endswith("sayHello"):
                canvas = Canvas("", lambda: None)
                canvas.scaleX = 4.0
                CallView(canvas, call).draw("orange", "yellow")
                mock_fillrect.assert_called_once_with(49, 22, 167, 21, 'orange')
                return
        raise ValueError("Could not find sayHello")


if __name__ == '__main__':
    unittest.main()
