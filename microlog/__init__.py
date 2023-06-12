#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from .microlog import info, warn, debug, error
from .microlog import start, stop
from .microlog import heap
from .microlog import enabled

try:
    from . import server
except:
    pass # the server is not included in the UI