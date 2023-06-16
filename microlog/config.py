#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import os
import time

EVENT_KIND_SYMBOL = 0
EVENT_KIND_CALL = 1
EVENT_KIND_STATUS = 2
EVENT_KIND_INFO = 3
EVENT_KIND_WARN = 4
EVENT_KIND_DEBUG = 5
EVENT_KIND_ERROR = 6
EVENT_KIND_CALLSITE = 7

kinds = [
    "Symbol",
    "Call",
    "Status",
    "Info",
    "Warn",
    "Debug",
    "Error",
    "Callsite",
]

statusDelay: float = 0.1
traceDelay: float = 0.01

IGNORE_MODULES = [
    "microlog.tracer",
    "microlog.microlog",
    "microlog",
    "importlib"
] 
