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
import os
import random
import sys
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
    def dumpASTs(self, index, moduleCount):
        self.simulateBlockingIO()
        for moduleIndex, moduleName in enumerate(list(sys.modules)[:moduleCount]):
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
            elif random.random() > 0.9:
                if moduleName == "re":
                    microlog.error(f"ERROR: this is an error message for module '{moduleName}'")  
                elif moduleName == "ast":
                    microlog.debug(f"DEBUG: this is used to debug code, something we need to fix with '{moduleName}'")
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