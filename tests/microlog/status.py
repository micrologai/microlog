#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import unittest

from microlog import config
from microlog import events
from microlog.status import Process
from microlog.status import Python
from microlog.status import StatusGenerator
from microlog.status import System


class StatusTest(unittest.TestCase):
    def test_getProcess(self):
        process: Process = StatusGenerator().getProcess()
        self.assertIsInstance(process, Process)
        self.assertGreaterEqual(process.cpu, 0)
        self.assertLessEqual(process.cpu, 100)

    def test_getSystem(self):
        system: System = StatusGenerator().getSystem()
        self.assertIsInstance(system, System)
        self.assertGreaterEqual(system.cpu, 0)
        self.assertGreater(system.memoryTotal, 0)
        self.assertGreater(system.memoryFree, 0)

    def test_getPython(self):
        python: Python = StatusGenerator().getPython()
        self.assertIsInstance(python, Python)
        self.assertGreater(python.moduleCount, 0)

    def test_sample(self):
        events.clear()
        status = StatusGenerator()
        status.sample()
        event = events.get()
        self.assertEqual(len(event), 5)
        kind, when, system, process, python = event
        self.assertEqual(kind, config.EVENT_KIND_STATUS)
        self.assertGreater(when, 0)

        self.assertEqual(len(system), 3)
        self.assertGreaterEqual(system[0], 0)
        self.assertGreater(system[1], 0)
        self.assertGreater(system[2], 0)

        self.assertEqual(len(process), 1)
        self.assertGreaterEqual(process[0], 0)

        self.assertEqual(len(python), 1)
        self.assertGreaterEqual(python[0], 0)


if __name__ == "__main__":
    unittest.main()
