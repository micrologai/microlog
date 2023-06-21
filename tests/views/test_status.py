
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
from dashboard.views.status import StatusView
from dashboard.canvas import Canvas


class TestStatusView(unittest.TestCase):
    def setUp(self):
        log.log.load(json.dumps({
            "calls": [],
            "markers": [],
            "statuses": [
                {
                    "when": 0.0007256449898704886,
                    "system": {
                        "cpu": 0.0,
                        "memoryTotal": 34359738368,
                        "memoryFree": 6210158592
                    },
                    "process": {
                        "cpu": 92.58930622475515,
                        "memory": 18571264
                    },
                    "python": {
                        "moduleCount": 180
                    },
                    "duration": 0
                },
            ],
            "begin": 297246.842675386
        }))
        self.canvas = Canvas("", lambda: None)
        self.status = StatusView(self.canvas, log.log.statuses[0])

    @unittest.mock.patch('dashboard.canvas.Canvas.toScreenDimension', return_value=10)
    @unittest.mock.patch('dashboard.canvas.Canvas.fillRect')
    @unittest.mock.patch('dashboard.canvas.Canvas.image')
    @unittest.mock.patch('dashboard.views.status.StatusView.drawCpu')
    @unittest.mock.patch('dashboard.views.status.StatusView.drawMemory')
    @unittest.mock.patch('dashboard.views.status.StatusView.drawModules')
    def test_drawAll(self, *mocks):
        views = [self.status]
        StatusView.drawAll(self.canvas, views)
        self.canvas.fillRect.assert_called_once()
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
