#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import unittest

from microlog import config
from microlog import log
from microlog.api import models
from microlog.models import Process
from microlog.models import Python
from microlog.tracer import StatusGenerator
from microlog.models import System


class StatusTest(unittest.TestCase):
    def setUp(self):
        models.start()

    def test_getProcess(self):
        generator = StatusGenerator()
        process: Process = generator.getProcess()
        self.assertIsInstance(process, Process)
        self.assertGreaterEqual(process.cpu, 0)
        self.assertLessEqual(process.cpu, 100)

    def test_getSystem(self):
        generator = StatusGenerator()
        system: System = generator.getSystem()
        self.assertIsInstance(system, System)
        self.assertGreaterEqual(system.cpu, 0)
        self.assertGreater(system.memoryTotal, 0)
        self.assertGreater(system.memoryFree, 0)

    def test_getPython(self):
        python: Python = StatusGenerator().getPython()
        self.assertIsInstance(python, Python)
        self.assertGreater(python.moduleCount, 0)

    def test_sample(self):
        log.clear()
        status = StatusGenerator()
        status.tick()
        event = log.buffer[0]
        self.assertEqual(event[0], config.EVENT_KIND_SYMBOL)
        event = log.buffer[1]
        self.assertEqual(event[0], config.EVENT_KIND_SYMBOL)
        event = log.buffer[2]
        self.assertEqual(event[0], config.EVENT_KIND_STATUS)
        kind, whenIndex, statusIndex = event
        self.assertEqual(kind, config.EVENT_KIND_STATUS)
        self.assertGreater(models.getSymbol(whenIndex), 0)

        import json
        system, process, python = json.loads(models.getSymbol(statusIndex))
        self.assertEqual(len(system), 3)
        self.assertGreaterEqual(system[0], 0)
        self.assertGreater(system[1], 0)
        self.assertGreater(system[2], 0)

        self.assertEqual(len(process), 2)
        self.assertGreaterEqual(process[0], 0)

        self.assertEqual(len(python), 1)
        self.assertGreaterEqual(python[0], 0)


if __name__ == "__main__":
    unittest.main()
