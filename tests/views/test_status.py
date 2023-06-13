
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

        from dashboard import canvas
        from microlog import log
        log.buffer = [
            [0, 383, 6.827] , # Symbol
            [0, 384, '[[0, 32.0, 3.6], [99, 0.0], [180]]'] , # Symbol
            [2, 383, 384] , # Status
        ]
        log.validate()
        self.canvas = canvas.Canvas("", lambda: None)

    @unittest.mock.patch('dashboard.canvas.Canvas.toScreenDimension', return_value=10)
    @unittest.mock.patch('dashboard.canvas.Canvas.fillRect')
    @unittest.mock.patch('dashboard.canvas.Canvas.image')
    @unittest.mock.patch('dashboard.views.status.StatusView.drawCpu')
    @unittest.mock.patch('dashboard.views.status.StatusView.drawMemory')
    @unittest.mock.patch('dashboard.views.status.StatusView.drawModules')
    def test_drawAll(self, *mocks):
        from dashboard.views import status
        from microlog import log
        view = status.StatusView(self.canvas, log.buffer[2])
        views = [view]
        status.StatusView.drawAll(self.canvas, views)
        self.canvas.fillRect.assert_called_once()
        status.StatusView.drawCpu.assert_called_once_with(self.canvas, views)
        status.StatusView.drawMemory.assert_called_once_with(self.canvas, views)
        status.StatusView.drawModules.assert_called_once_with(self.canvas, views)

    @unittest.mock.patch('dashboard.canvas.Canvas.polygon')
    def test_drawModules_calls_polygon(self, *mocks):
        from dashboard.views import status
        from microlog import log
        view = status.StatusView(self.canvas, log.buffer[2])
        views = [view]
        view.python.moduleCount = 10
        status.StatusView.drawModules(self.canvas, views)
        self.canvas.polygon.assert_called_once()

    @unittest.mock.patch('dashboard.canvas.Canvas.polygon')
    def test_drawMemory_calls_polygon(self, *mocks):
        from dashboard.views import status
        from microlog import log
        view = status.StatusView(self.canvas, log.buffer[2])
        views = [view]
        view.process.memory = 300
        status.StatusView.drawMemory(self.canvas, views)
        self.canvas.polygon.assert_called_once()

    @unittest.mock.patch('dashboard.canvas.Canvas.polygon')
    @unittest.mock.patch('dashboard.canvas.Canvas.region')
    def test_drawCpu_calls_polygon_and_region(self, *mocks):
        from dashboard.views import status
        from microlog import log
        view = status.StatusView(self.canvas, log.buffer[2])
        views = [view]
        view.process.cpu = 55
        status.StatusView.drawCpu(self.canvas, views)
        self.canvas.polygon.assert_called_once()
        self.canvas.region.assert_called_once()


if __name__ == "__main__":
    unittest.main() 
