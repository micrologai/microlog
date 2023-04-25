#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

from microlog import symbols
from microlog import events

class Meta():
    def __init__(self, kind: int, when:float, main: str):
        self.when = when
        self.kind = kind
        self.main = main

    @classmethod
    def unmarshall(cls, event: list) -> Meta:
        kind, when, mainIndex = event
        return Meta(
            kind,
            when,
            symbols.get(mainIndex),
        )

    def marshall(self):
        events.put([
            self.kind,
            self.when,
            symbols.index(self.main),
        ])
