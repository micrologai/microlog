#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import inspect
import json
import types

from microlog import config
from microlog import events
from microlog import symbols

class Span():
    def __init__(self, when: float, name: str, duration: float, arguments=[]):
        self.when = when
        self.name = name
        self.duration = duration
        self.arguments = arguments

    @classmethod
    def load(cls, event):
        _, when, nameIndex, duration, arguments = event
        return Span(when, symbols.get(nameIndex), duration, arguments)

    def save(self):
        events.put([
            config.EVENT_KIND_SPAN,
            round(self.when, 3),
            symbols.index(self.name),
            round(self.duration, 3),
            json.dumps(self.arguments)
        ])


def describe(value):
    if value is None:
        return None
    valueType = type(value)
    if valueType is str:
        return (f"{value[:11]}..." if len(value) > 11 else value).replace("\"", "")
    if valueType in [int, float, bool]:
        return value
    elif valueType in [dict, list]:
        return f"{valueType.__name__}[{len(value)}]"
    elif inspect.ismethod(value):
        return f"<method {value.__name__}>"
    elif inspect.isfunction(value):
        return f"<function {value.__name__}>"
    else:
        return f"<{value.__class__.__name__}>"


def freezeArguments(function, args, argv):
    signature = inspect.signature(function)
    arguments = dict(
        (param.name, value)
        for param, value in zip(signature.parameters.values(), args)
    )
    arguments.update(argv)
    return json.dumps([
        ( key, describe(value) )
        for key, value in arguments.items()
        if not key in ["args", "argv"]
    ])