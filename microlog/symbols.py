#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import collections

from microlog import events
from microlog import config

indexToSymbol = {}
symbolToIndex = collections.defaultdict(lambda: len(indexToSymbol))

def index(symbol):
    symbol = symbol.replace("\n", "\\n")
    if not symbol in symbolToIndex:
        events.put((
            config.EVENT_KIND_SYMBOL,
            symbolToIndex[symbol],
            symbol.replace("\"", "\\\"")
        ))
        indexToSymbol[symbolToIndex[symbol]] = symbol

    return symbolToIndex[symbol]


def load(event):
    # typical event: [0, 144, "inspect psutil"]
    put(event[1], event[2])


def put(index, symbol):
    symbol = symbol.replace("\n", "\\n")
    indexToSymbol[index] = symbol


def get(index):
    return indexToSymbol[index]