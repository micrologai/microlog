#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import ast
import inspect
import sys
import random
import time


def simulateIO(s):
    if random.random() > 0.95:
        time.sleep(s)


def countItems(index, moduleName):
    return index, len(dir(moduleName))


def countModules():
    for n in range(75):
        [countItems(n, moduleName) for n, moduleName in enumerate(list(sys.modules))]


class Example():
    def getAst(self, n, moduleName):
        try:
            source = inspect.getsource(sys.modules[moduleName])
        except:
            print("no source", moduleName)
            source = ""
        return self.parse(n, moduleName, source)

    def parse(self, n, module, source):
        return ast.parse(source)

    def simulateBlockingIO(self):
        simulateIO(1.5)

    def dumpASTs(self, run, index, moduleCount):
        self.simulateBlockingIO()

    def parseASTs(self, runCount, moduleCount):
        for repeatCount in range(10):
            self.dumpASTs(runCount, repeatCount, moduleCount)

    def run(self, runCount):
        countModules()
        time.sleep(0.5)
        self.parseASTs(runCount, 100)


example = Example()


def main():
    print("EXAMPLE: start")
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    for n in range(1, runs + 1):
        print("run", n, "of", runs)
        example.run(n)
    print("EXAMPLE: done")
    
main()