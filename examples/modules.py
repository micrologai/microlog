#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import sys
sys.path.insert(0, ".")
            
import microlog.api as api
import time
import sys

def loadModule(name):
    __import__(name)


def load(name):
    try:
        start = time.time()
        moduleCount = len(sys.modules)
        loadModule(name)
        duration = round(time.time() - start, 1)
        msg = api.info if duration < 0.3 else api.error
        msg(f"{name} - {len(sys.modules) - moduleCount} modules - {duration}s")
    except:
        pass

load('bleach')
load('certifi')
load('click')
load('cycler')
load('decorator')
load('docutils')
load('exceptiongroup')
load('fsspec')
load('idna')
load('iniconfig')
load('jedi')
load('kiwisolver')
load('matplotlib')
load('mpmath')
load('multidict')
load('networkx')
load('nltk')
load('pandas')
load('pluggy')
load('py')
load('pydantic')
load('pytest')
load('sqlalchemy')
load('sympy')
load('tomli')
load('tqdm')
load('yarl')