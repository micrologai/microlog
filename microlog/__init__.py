#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

__version__ = "1.3.3"

from .api import info, warn, debug, error
from .api import start, stop
from .api import heap
from .api import enabled

try:
    from . import server
except:
    pass # the server is not included in the UI