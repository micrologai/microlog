#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import unittest

from microlog import config
from microlog import log
from microlog.microlog import symbols
from microlog.models import Process
from microlog.models import Python
from microlog.models import StatusGenerator
from microlog.models import System


class StatusTest(unittest.TestCase):
    def setUp(self):
        symbols.clear()
        log.clear()

    def test_getProcess(self):
        generator = StatusGenerator()
        generator.start()
        process: Process = generator.getProcess()
        self.assertIsInstance(process, Process)
        self.assertGreaterEqual(process.cpu, 0)
        self.assertLessEqual(process.cpu, 100)

    def test_getSystem(self):
        generator = StatusGenerator()
        generator.start()
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
        status = StatusGenerator()
        status.start()
        status.tick()
        event = log.get()
        self.assertEqual(event[0], config.EVENT_KIND_SYMBOL)
        event = log.get()
        self.assertEqual(event[0], config.EVENT_KIND_SYMBOL)
        event = log.get()
        self.assertEqual(event[0], config.EVENT_KIND_STATUS)
        kind, whenIndex, statusIndex = event
        self.assertEqual(kind, config.EVENT_KIND_STATUS)
        self.assertGreater(getSymbol(whenIndex), 0)

        import json
        system, process, python = json.loads(getSymbol(statusIndex))
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
