
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
from dashboard.views.status import StatusView
from dashboard.canvas import Canvas

LOG = open(os.path.join(os.path.dirname(__file__), "helloworld.log")).read()

class TestStatusView(unittest.TestCase):
    def setUp(self):
        log.log.load(LOG)
        self.canvas = Canvas("", lambda: None)
        self.status = StatusView(self.canvas, log.log.statuses[0])

    @unittest.mock.patch('dashboard.canvas.Canvas.toScreenDimension', return_value=10)
    @unittest.mock.patch('dashboard.views.status.StatusView.drawCpu')
    @unittest.mock.patch('dashboard.views.status.StatusView.drawMemory')
    @unittest.mock.patch('dashboard.views.status.StatusView.drawModules')
    def test_drawAll(self, *mocks):
        views = [self.status]
        StatusView.drawAll(self.canvas, views)
        StatusView.drawCpu.assert_called_once_with(self.canvas, views)
        StatusView.drawMemory.assert_called_once_with(self.canvas, views)
        StatusView.drawModules.assert_called_once_with(self.canvas, views)

    @unittest.mock.patch('dashboard.canvas.Canvas.polygon')
    def test_drawModules_calls_polygon(self, *mocks):
        StatusView.drawModules(self.canvas, [self.status])
        self.canvas.polygon.assert_called_once()

    @unittest.mock.patch('dashboard.canvas.Canvas.polygon')
    def test_drawMemory_calls_polygon(self, *mocks):
        StatusView.drawMemory(self.canvas, [self.status])
        self.canvas.polygon.assert_called_once()

    @unittest.mock.patch('dashboard.canvas.Canvas.polygon')
    @unittest.mock.patch('dashboard.canvas.Canvas.region')
    def test_drawCpu_calls_polygon_and_region(self, *mocks):
        StatusView.drawCpu(self.canvas, [self.status])
        self.canvas.polygon.assert_called_once()
        self.canvas.region.assert_called_once()


if __name__ == "__main__":
    unittest.main() 
