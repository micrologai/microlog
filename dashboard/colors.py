#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from dashboard import profiler

colors = {}

CANDY = [
    "#e09550", "#e2d165", "#e0bb5a", "#dab5fc", "#e4664e",
    "#4da2f7", "#4da2f7", "#4eb28e", "#dab5fc", "#dab5fc",
]

DISCO = [
    '#007baa', '#6610f2', '#6f42c1', '#e83e8c', '#dc3545',
    '#7fde14', '#c1aa07', '#28a745', '#20c997', '#17a2b8',
]

PASTEL = [
    '#acebff', '#ffb666', '#fffa99', '#e6e6e7', '#e6e6e7',
    '#6ea1e2', '#efc1f2', '#bad8f7', '#f7e5ba'
]


def index(name, palette=PASTEL):
    try:
        ordinals = ord(name[0]) + ord(name[round(len(name) / 2)]) + ord(name[-1])
        return ordinals % len(palette)
    except:
        return 0


@profiler.profile("colors.getColor")
def getColor(name, palette=PASTEL):
    if not name in colors:
        colors[name] = palette[index(name)]
    return colors[name]