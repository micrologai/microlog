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
EVENT_KIND_MARKER = 8
EVENT_KIND_STACK = 9
EVENT_KIND_CPU = 10
EVENT_KIND_MEMORY = 11
EVENT_KIND_SYSTEM_CPU = 12
EVENT_KIND_MEMORY_FREE = 13
EVENT_KIND_MEMORY_TOTAL = 14
EVENT_KIND_MODULE_COUNT = 15

kinds = [
    "Symbol",
    "Call",
    "Status",
    "Info",
    "Warn",
    "Debug",
    "Error",
    "Callsite",
    "Marker",
    "Stack",
]

statusDelay: float = 0.01
traceDelay: float = 0.01

IGNORE_MODULES = [
    "microlog.tracer",
    "microlog.microlog",
    "microlog",
    "importlib"
] 

application = ""
version = ""