#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import ast
import inspect
import unittest


class TestPrint(unittest.TestCase):

    def check(self, module):
        source = inspect.getsource(module)
        tree = ast.dump(ast.parse(source), indent=4)
        self.assertFalse("func=Name(id='print', ctx=Load())" in tree, f"Module {module} contains a print statement, please replace with sys.stdout.write")

    def test_init(self):
        import microlog
        self.check(microlog)

    def test_config(self):
        from microlog import config
        self.check(config)

    def test_log(self):
        from microlog import log
        self.check(log)

    def test_models(self):
        from microlog import models
        self.check(models)

    def test_tracer(self):
        from microlog import tracer
        self.check(tracer)



if __name__ == '__main__':
    unittest.main()
