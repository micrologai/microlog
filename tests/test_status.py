#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import unittest

from microlog import log
from microlog.tracer import StatusGenerator


class StatusTest(unittest.TestCase):
    def test_sample(self):
        status = StatusGenerator()
        status.tick()
        self.assertGreaterEqual(len(log.log.statuses), 2)

        status = log.log.statuses[0]
        self.assertGreaterEqual(status.cpu, 0)
        self.assertGreater(status.memoryTotal, 0)
        self.assertGreater(status.memoryFree, 0)
        self.assertGreaterEqual(status.systemCpu, 0)
        self.assertGreaterEqual(status.memory, 0)
        self.assertGreater(status.moduleCount, 0)


if __name__ == "__main__":
    unittest.main()