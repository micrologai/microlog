#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

__version__ = "1.3.34"

import sys
import subprocess

try:
    import appdata, psutil
except:
    try:
        install = [ sys.executable, '-m', 'pip', 'install', 'appdata', 'psutil' ]
        if sys.argv[-3:] != install[-3:]:
            subprocess.check_call(install)
            sys.stdout.write("[Microlog] installed 'appdata' and 'psutil'\n")
    except:
        pass # this will fail on pyscript, which is OK

from .api import info, warn, debug, error
from .api import start, stop
from .api import heap
from .api import enabled

try:
    from . import server
except:
    pass # the server is not included in the UI
