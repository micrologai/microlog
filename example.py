#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import microlog

microlog.start(
    application="Example",
    version=1.0,
    info="Just testing",
    showInBrowser=True,
    verbose=True,
)

import ast
import inspect
import random
import sys
import time

ADD_SLEEP = True

def sleep(s):
    if ADD_SLEEP:
        time.sleep(s)

def countItems(index, moduleName):
    sleep(0.01)
    return len(dir(moduleName))

@microlog.trace
def countModules(moduleCount):
    microlog.info(f"INFO: counting modules")
    return [countItems(n, moduleName) for n, moduleName in enumerate(list(sys.modules)[:moduleCount])]

class Example():
    def getAst(self, n, moduleName):
        try:
            source = inspect.getsource(sys.modules[moduleName])
        except:
            source = ""
        return self.parse(n, moduleName, source)

    def parse(self, n, module, source):
        return ast.parse(source)

    def simulateBlockingIO(self):
        if random.random() > 0.95:
            sleep(1.5)

    @microlog.trace
    def dumpASTs(self, index, moduleCount):
        self.simulateBlockingIO()
        for moduleIndex, moduleName in enumerate(list(sys.modules)[:moduleCount]):
            if random.random() > 0.9:
                if moduleName == "sys":
                    microlog.warn(f"WARNING: this is a warning")
                if moduleName == "re":
                    microlog.error(f"ERROR: this is an error message")  
                if moduleName == "ast":
                    microlog.debug(f"DEBUG: this is used to debug code")
            ast.dump(self.getAst(moduleIndex, moduleName))

    @microlog.trace
    def parseASTs(self, moduleCount):
        for repeatCount in range(10):
            self.dumpASTs(repeatCount, moduleCount)

    @microlog.trace
    def run(self, runCount):
        countModules(50)
        self.parseASTs(100)


example = Example()

def main():
    print("EXAMPLE: start")
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    for n in range(1, runs + 1):
        print("run", n, "of", runs)
        example.run(n)
    print("EXAMPLE: done")
    
main()