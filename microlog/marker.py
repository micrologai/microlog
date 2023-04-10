#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

from microlog import symbols
from microlog import events

from typing import List
from typing import Any

class MarkerModel():
    def __init__(self, kind: int, when:float, message: str, stack:List[str]):
        self.when = when
        self.kind = kind
        self.message = message
        self.stack = stack
        self.duration = 0.1

    @classmethod
    def load(cls, event: list) -> MarkerModel:
        kind, when, messageIndex, stack = event
        return MarkerModel(
            kind,
            when,
            symbols.get(messageIndex),
            [ symbols.get(index).replace("\\n", "\n") for index in stack ],
        )

    def save(self):
        events.put([
            self.kind,
            self.when,
            symbols.index(self.message),
            [ symbols.index(line) for line in self.stack[:-2] if not "microlog/microlog/__init__.py" in line ],
        ])