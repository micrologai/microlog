#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import unittest
from unittest.mock import MagicMock


class TestCallView(unittest.TestCase):

    def setUp(self):
        import sys
        sys.modules["js"] = MagicMock()
        sys.modules["pyodide"] = MagicMock()
        import microlog
        from microlog import log
        from microlog import models
        from dashboard.views import View
        microlog.stop()
                
        models.start()
        View.start()
        log.buffer = [
            (0, 10, '/Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/socket.py'),
            (0, 11, 'socket..create_connection'),
            (7, 0, 10, 824, 11),
            (0, 12, 'visualstudio_py_testlauncher.py'),
            (0, 13, 'visualstudio_py_testlauncher..main'),
            (7, 1, 12, 289, 13),
            (0, 14, 140704642332224),
            (0, 15, 0.035),
            (0, 16, 0.011),
            (1, 14, 0, 1, 2, 15, 16),  # call
        ]
        log.validate()

    def test_get_full_name(self):
        from dashboard.views.call import CallView
        from microlog import log
        self.assertEqual(len(log.buffer), 10)
        view = CallView(None, log.buffer[9])
        self.assertEqual(view.getFullName(), "socket..create_connection")

    def test_get_short_name(self):
        from dashboard.views.call import CallView
        from microlog import log
        view = CallView(None, log.buffer[9])
        self.assertEqual(view.getShortName(), "create_connection")

    def test_is_anomaly(self):
        from dashboard.views.call import CallView
        from microlog import log
        view = CallView(None, log.buffer[9])
        anomalies = [1, 2]
        self.assertTrue(view.isAnomaly(1, anomalies))
        self.assertFalse(view.isAnomaly(3, anomalies))


if __name__ == '__main__':
    unittest.main()
