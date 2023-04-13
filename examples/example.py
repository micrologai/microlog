#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import sys
sys.path.insert(0, ".")

import ast
import inspect
import microlog
import os
import random
import time


def simulateIO(s):
    if random.random() > 0.95:
        time.sleep(s)


@microlog.trace
def countItems(index, moduleName):
    simulateIO(0.01)
    return index, len(dir(moduleName))


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
        simulateIO(1.5)

    @microlog.trace
    def dumpASTs(self, run, index, moduleCount):
        self.simulateBlockingIO()
        for moduleIndex, moduleName in enumerate(list(sys.modules)[:moduleCount]):
            if random.random() > 0.1:
                continue
            if moduleName == "datetime":
                module = sys.modules[moduleName]
                filename = inspect.getfile(module)
                itemcount = len(dir(module))
                microlog.warn(f"""
                    # Example warning
                    
                    This is a warning for {index}, {moduleIndex}, '{moduleName}'.
                    The text in this message can be arbitrary complex. 

                    There is no need to add a stacktrace, as microlog.ai already adds those.

                    Just explain the context, and add some details of the context,
                    such as:

                      - the module's filename: {filename}. 
                      - the file size: {os.stat(filename).st_size} bytes.
                      - the module has {itemcount} items in it.
                """)
            if moduleName == "re":
                microlog.error(f"ERROR: this is an error message for module '{moduleName}'")  
            elif run > 5 and moduleName == "genericpath":
                microlog.debug(f"""
                    This is used to debug code. For this example, we demonstrate, how a certain
                    import statement has impact on module count, memory, and CPU. 
                    
                    We import the
                    following two modules:

                      - pytest
                      - mock

                    Total module count should go up from around 200 modules to over 300 for the first occurrence of this call.

                    Notice the yellow line in the status bar that indicates module count growth over time.
                """)
                import pytest
                import mock
            ast.dump(self.getAst(moduleIndex, moduleName))

    @microlog.trace
    def parseASTs(self, runCount, moduleCount):
        for repeatCount in range(10):
            self.dumpASTs(runCount, repeatCount, moduleCount)

    @microlog.trace
    def run(self, runCount):
        countModules(50)
        self.parseASTs(runCount, 100)


example = Example()


def main():
    print("EXAMPLE: start")
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    for n in range(1, runs + 1):
        print("run", n, "of", runs)
        example.run(n)
    print("EXAMPLE: done")
    

with microlog.enabled(application="Example", version=1.1, info="Incrased the version", showInBrowser=True, verbose=True):
    main()