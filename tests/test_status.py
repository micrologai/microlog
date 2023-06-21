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
        status = StatusGenerator()
        status.tick()
        self.assertGreaterEqual(len(log.log.statuses), 3)

        status = log.log.statuses[0]
        self.assertGreaterEqual(status.system.cpu, 0)
        self.assertGreater(status.system.memoryTotal, 0)
        self.assertGreater(status.system.memoryFree, 0)
        self.assertGreaterEqual(status.process.cpu, 0)
        self.assertGreaterEqual(status.process.memory, 0)
        self.assertGreater(status.python.moduleCount, 0)


if __name__ == "__main__":
    unittest.main()