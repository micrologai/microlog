#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import unittest
from unittest.mock import MagicMock


class TestCallView(unittest.TestCase):

    def setUp(self):
        import json
        import sys
        sys.modules["js"] = MagicMock()
        sys.modules["pyodide"] = MagicMock()
        import microlog
        microlog.stop()
        microlog.log.log.load(json.dumps({
            "calls": [
                {
                    "when": 0.038782909978181124,
                    "threadId": 140704642332224,
                    "callSite": {
                        "filename": "/Library/Frameworks/Python.framework/Versions/3.10/lib/python3.10/logging/__init__.py",
                        "lineno": 1465,
                        "name": "logging.Logger.debug"
                    },
                    "callerSite": {
                        "filename": "/Users/laffra/dev/micrologai/microlog/~/dev/micrologai/microlog/examples/helloworld.py",
                        "lineno": 24,
                        "name": "examples.helloworld..sayHello"
                    },
                    "depth": 2,
                    "duration": 0.0012418510159477592
                }
            ],
            "markers": [],
            "statuses": [],
            "begin": 297246.842675386
        }))

    def test_get_full_name(self):
        from dashboard.views.call import CallView
        from microlog import log
        view = CallView(None, log.log.calls[0])
        self.assertEqual(view.getFullName(), "logging.Logger.debug")

    def test_get_short_name(self):
        from dashboard.views.call import CallView
        from microlog import log
        view = CallView(None, log.log.calls[0])
        self.assertEqual(view.getShortName(), "debug")

    def test_is_anomaly(self):
        from dashboard.views.call import CallView
        from microlog import log
        view = CallView(None, log.log.calls[0])
        anomalies = [1, 2]
        self.assertTrue(view.isAnomaly(1, anomalies))
        self.assertFalse(view.isAnomaly(3, anomalies))


if __name__ == '__main__':
    unittest.main()
