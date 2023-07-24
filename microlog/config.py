#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import os
import time

EVENT_KIND_SECTION = "#"
EVENT_KIND_CALL = 1
EVENT_KIND_STATUS = 2
EVENT_KIND_INFO = 3
EVENT_KIND_WARN = 4
EVENT_KIND_DEBUG = 5
EVENT_KIND_ERROR = 6
EVENT_KIND_CALLSITE = 7
EVENT_KIND_MARKER = 8
EVENT_KIND_STACK = 9
EVENT_KIND_SYMBOL = 10

kinds = [
    "Section",
    "Call",
    "Status",
    "Info",
    "Warn",
    "Debug",
    "Error",
    "Callsite",
    "Marker",
    "Stack",
    "Symbol",
]

statusDelay: float = float(os.environ.get("MICROLOG_STATUS_DELAY", 0.1))
sampleDelay: float = float(os.environ.get("MICROLOG_SAMPLE_DELAY", 0.1))

IGNORE_MODULES = [
    "microlog.api",
    "microlog.tracer",
    "microlog.microlog",
    "microlog",
] 

application = ""