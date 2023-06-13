#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import unittest
from unittest.mock import MagicMock


class TestCallView(unittest.TestCase):
    BUFFER = [
        (0, 10, '/Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/socket.py'),
        (0, 11, 'socket..create_connection'),
        (7, 0, 10, 824, 11),
        (0, 12, 'visualstudio_py_testlauncher.py'),
        (0, 13, 'visualstudio_py_testlauncher..main'),
        (7, 1, 12, 289, 13),
        (0, 14, 140704642332224),
        (0, 15, 0.035),
        (0, 16, 0.011),
        (1, 14, 0, 1, 2, 15, 16),
        (0, 17, 'socket..getaddrinfo'),
        (7, 2, 10, 955, 17),
        (1, 14, 2, 0, 3, 15, 16),               # call
        (0, 18, 'encodings/__init__.py'),       # symbol
        (0, 19, 'encodings..search_function'),  # symbol
        (7, 3, 18, 99, 19),                     # callsite
        (1, 14, 3, 2, 4, 15, 16),               # call
    ]

    def setUp(self):
        import sys
        sys.modules["js"] = MagicMock()
        sys.modules["pyodide"] = MagicMock()

        from microlog import log
        from microlog import config
        from dashboard.views.call import CallView
                
        log.buffer = TestCallView.BUFFER
        log.validate()
        for event in log.buffer:
            if event[0] == config.EVENT_KIND_CALL:
                self.call_view = CallView(None, event)
                break

    def test_get_full_name(self):
        self.assertEqual(self.call_view.getFullName(), "socket..create_connection")

    def test_get_short_name(self):
        self.assertEqual(self.call_view.getShortName(), "create_connection")

    def test_is_anomaly(self):
        anomalies = [1, 2]
        self.assertTrue(self.call_view.isAnomaly(1, anomalies))
        self.assertFalse(self.call_view.isAnomaly(3, anomalies))

if __name__ == '__main__':
    unittest.main()
