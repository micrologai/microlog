import os
import re
import sys

def getApplication():
    return re.sub("/|\.py$", "-", sys.argv[0])[:-1]

def getVersion():
    path = os.path.abspath(sys.argv[0])
    while path != "/":
        setup = os.path.join(path, "setup.py")
        if os.path.exists(setup):
            import ast
            tree = ast.parse(open(setup).read())
            for line in ast.dump(tree, indent=4).split("\n"):
                if re.search("value='[0-9.]*'", line):
                    return re.sub(r".*value='([0-9.]*)'.*", r"\1", line)
        path = os.path.dirname(path)
    return "0.0.0"

def getEnvironment():
    return "dev"

sys.path.insert(0, ".")
sys.path.append("/Users/laffra/dev/micrologai/microlog")
import microlog
try:
    microlog.start(getApplication(), getVersion(), getEnvironment(), verbose=False)
except:
    import traceback
    traceback.print_exc()