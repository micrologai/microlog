#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

class Settings():
    application: str = ""
    version: str = ""
    environment: str = ""
    info: str = ""
    traceDelay: float = 0.005
    statusDelay: float = 0.05

    def __init__(self,
                 application: str = "",
                 version: str = "",
                 environment: str = "",
                 info: str = "",
                 traceDelay: float = 0.005,
                 statusDelay: float = 0.05):
        self.application = application
        self.version = version
        self.environment = environment
        self.info = info
        self.traceDelay = traceDelay
        self.statusDelay = statusDelay

current = Settings()