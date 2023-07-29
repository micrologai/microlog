#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import os

PROFILING_MODE_SAMPLING = 1
PROFILING_MODE_PRECISE = 2

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
profileDelay: float = float(os.environ.get("MICROLOG_PROFILE_DELAY", 0.5))

IGNORE_MODULES = [
    "microlog.api",
    "microlog.tracer",
    "microlog.microlog",
    "microlog.models",
    "microlog",
] 

application = ""
mode = PROFILING_MODE_SAMPLING if os.environ.get("MICROLOG_PROFILING_MODE", "SAMPLING") == "SAMPLING" else PROFILING_MODE_PRECISE