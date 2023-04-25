#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

from collections import defaultdict
import js
import json
import pyodide
from typing import List

from microlog.stack import Call
from microlog import meta
from dashboard import colors


class Node():
    def __init__(self):
        self.index = -1
        self.depth = -1
        self.count = 1

    def setName(self, moduleName, className):
        self.moduleName = moduleName
        self.className = className
        self.name = f"{moduleName}.{className}" if className else moduleName
        return self

    def setIndex(self, index):
        if self.index == -1:
            self.index = index
        return self

    def setDepth(self, depth):
        self.depth = depth
        return self

    def __hash__(self):
        return self.name.__hash__()

    def __eq__(self, other):
        return other.name == self.name


class Edge():
    def __init__(self):
        self.counts = defaultdict(int)

    def connect(self, fromNode: Node, toNode: Node, function: str):
        self.fromNode = fromNode
        self.toNode = toNode
        self.counts[function] += 1
        return self

    def __repr__(self):
        return f"{self.fromNode.name} => {self.toNode.name}"

    def __hash__(self):
        return self.__repr__().__hash__()

    def __eq__(self, other):
        return other.__repr__() == self.__repr__()


class Design():
    LEVEL1 = 0
    LEVEL2 = 20
    LEVEL3 = 40
    SKIP = set([
        "importlib",
        "importlib._bootstrap",
        "importlib._bootstrap_external",
        "importlib._bootstrap_external.FileFinder",
        "importlib._bootstrap_external.SourceFileLoader",
        "zipImport.zipImporter",
    ])
    def __init__(self):
        self.calls: List[Call] = []
        self.nodes = defaultdict(Node)
        self.edges = defaultdict(Edge)
        self.meta = meta.Meta(0, 0, "")

    def setMeta(self, meta: meta.Meta):
        self.meta = meta

    def getNode(self, name, depth):
        parts = name.split(".")
        cls = parts[-2]
        module = ".".join(parts[:-2])
        if False and module in self.SKIP:
            return None
        return self.nodes[f"{module}.{cls}"].setName(module, cls).setIndex(len(self.nodes)).setDepth(depth)

    def getEdge(self, fromNode, toNode, function):
        if not fromNode or not toNode or fromNode is toNode:
            return None
        key = f"{fromNode.name}=>{toNode.name}"
        return self.edges[key].connect(fromNode, toNode, function)

    def addCall(self, call: Call):
        self.calls.append(call)
        fromNode = self.getNode(call.callerSite.name, call.depth)
        toNode = self.getNode(call.callSite.name, call.depth)
        function = call.getShortName()
        self.getEdge(fromNode, toNode, function)

    def draw(self):
        nodes = {}
        edges = {}
        edgeCount = len(self.edges)
        level = 3 if edgeCount < self.LEVEL3 else 2 if edgeCount < self.LEVEL2 else 1
        def cluster(node):
            if level == 3 or node.name.startswith(self.meta.main):
                name, cls = node.name, node.className
            elif level == 2:
                name, cls = ".".join(node.name.split(".")[:-1]), ""
            else:
                name, cls = node.name.split(".")[0], ""
            if name in nodes:
                nodes[name].count += 1
                return nodes[name]
            node = Node().setName(name, cls).setIndex(len(nodes))
            nodes[name] = node
            return node

        liveNodes = set()
        for edge in reversed(self.edges.values()):
            fromNode = cluster(edge.fromNode)
            toNode = cluster(edge.toNode)
            if fromNode == toNode:
                continue
            for function, count in edge.counts.items():
                if function in ["__init__", "__getattr__", "__get__", "__str__", "__call__", "<module>"]:
                    continue
                liveNodes.add(fromNode)
                liveNodes.add(toNode)
                edges[(fromNode.index, toNode.index, function)] = {
                    "from": fromNode.index,
                    "to": toNode.index,
                    "label": function,
                    "value": count,
                    "font": {
                        "color": "orange",
                        "strokeWidth": 0,
                    },
                    "scaling": {
                        "max": 5,
                        "label": {
                            "max": 14,
                            "enabled": False,
                        },
                    },
                    "arrows": {
                        "to": {
                            "enabled": True,
                            "type": "arrow",
                        },
                    },
                }
        js.drawGraph(json.dumps({
            "nodes": [
                {
                    "id": node.index,
                    "label": node.name,
                    "level": node.depth,
                    "shape": "circularImage" if self.getImage(node) else "box",
                    "borderWidth": 2,
                    "value": node.count,
                    "size": 30,
                    "font": { "color": "white" },
                    "image": self.getImage(node),
                    "color": {
                        "border": colors.getColor(node.name, colors.DISCO),
                        "background": "darkgreen" if node.name in ["__main__", self.meta.main] else colors.getColor(node.name, colors.DISCO),
                        "highlight": { "border": "yellow", "background": "green" },
                        "hover": { "border": "orange", "background": "grey" },
                    },
                    "imagePadding": { "left": 2, "top": 2, "right": 2, "bottom": 8 },
                } for node in liveNodes ],
            "edges": list(edges.values()),
        }))

    def getImage(self, node):
        if node.name in images:
            return images[node.name]
        topName = node.name.split(".")[0]
        if topName in images:
            return images[topName]


images = {
    "runpy": "/images/icons/python.png",
    "matplotlib": "/images/icons/matplotlib.png",
    "matplotlib_inline": "/images/icons/matplotlib.png",
    "squarify": "/images/icons/squarify.png",
    "pandas": "/images/icons/pandas.png",
    "numpy": "/images/icons/numpy.png",
    "asyncio": "/images/icons/asyncio.png",
    "pyparsing": "/images/icons/pyparsing.png",
    "ssl": "/images/icons/ssl.png",
    "http": "/images/icons/http.png",
    "pluggy": "/images/icons/pluggy.webp",
    "pytest": "/images/icons/pytest.png",
    "testing_tools": "/images/icons/pytest.png",
    "_pytest": "/images/icons/pytest.png",
    "networkx": "/images/icons/networkx.png",
    "re": "/images/icons/re.png",
    "sre_compile": "/images/icons/re.png",
    "sre_parse": "/images/icons/re.png",
    "dataclasses": "/images/icons/dataclasses.png",
    "tornado": "/images/icons/tornado.png",
    "urllib": "/images/icons/urllib.png",
    "guppy": "/images/icons/guppy.png",
    "zmq": "/images/icons/zmq.png",
    "IPython": "/images/icons/jupyter.png",
    "jupyter_client": "/images/icons/jupyter.png",
    "ipykernel": "/images/icons/jupyter.png",
    "Jupyter": "/images/icons/jupyter.png",
    "microlog": "/images/icons/microlog.png",
    "examples": "/images/icons/microlog.png",
}

def zoom():
    graph = js.jQuery("#graph")
    if graph.attr("zoomed"):
        js.resizeGraph(200, 200)
        graph.attr("zoomed", "")
    else:
        width = js.jQuery("body").width() * 0.75
        height = js.jQuery("body").height() * 0.75
        js.resizeGraph(width, height)
        graph.attr("zoomed", "zoomed")

js.jQuery("#graph-zoom").click(pyodide.ffi.create_proxy(lambda event: zoom()))
