#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

from collections import defaultdict
import js # type: ignore
import json
from typing import List

from microlog.models import Call
from dashboard import profiler
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
        self.duration = defaultdict(float)

    def connect(self, fromNode: Node, toNode: Node, function: str, duration: int):
        self.fromNode = fromNode
        self.toNode = toNode
        self.counts[function] += 1
        self.duration[function] += duration
        return self

    def __repr__(self):
        return f"{self.fromNode.name} => {self.toNode.name}"

    def __hash__(self):
        return self.__repr__().__hash__()

    def __eq__(self, other):
        return other.__repr__() == self.__repr__()


class Design():
    LEVEL1 = 0
    LEVEL2 = 50
    LEVEL3 = 100

    @profiler.profile("Design.__init__")
    def __init__(self, calls):
        self.nodes = defaultdict(Node)
        self.edges = defaultdict(Edge)
        self.calls: List[Call] = []
        for call in calls:
            self.addCall(call)

    def getNode(self, name, depth):
        parts = name.split(".")
        cls = parts[-2]
        module = ".".join(parts[:-2])
        return self.nodes[f"{module}.{cls}"].setName(module, cls).setIndex(len(self.nodes)).setDepth(depth)

    def getEdge(self, fromNode, toNode, function, duration):
        if not fromNode or not toNode:
            return None
        key = f"{fromNode.name}=>{toNode.name}"
        return self.edges[key].connect(fromNode, toNode, function, duration)

    def addCall(self, call: Call):
        self.calls.append(call)
        fromNode = self.getNode(call.callerSite.name, call.depth)
        toNode = self.getNode(call.callSite.name, call.depth)
        function = call.getShortName()
        self.getEdge(fromNode, toNode, function, call.duration)


    def draw(self):
        nodes = {}
        edges = {}
        edgeCount = len(self.edges)
        level = 3 if edgeCount > self.LEVEL3 else 2 if edgeCount > self.LEVEL2 else 1
        def cluster(node):
            if level == 1:
                name, cls = node.name, node.className
            elif level == 2:
                name, cls = ".".join(node.name.split(".")[:-1]), ""
            else:
                name, cls = node.name.split(".")[0], ""
            if name in nodes:
                nodes[name].count += 1
                return nodes[name]
            node = Node().setName(name, cls).setIndex(len(nodes))
            node.selfReference = 0
            nodes[name] = node
            return node

        liveNodes = set()
        calls = []
        for edge in reversed(self.edges.values()):
            fromNode = cluster(edge.fromNode)
            toNode = cluster(edge.toNode)
            if fromNode == toNode and level > 1:
                continue
            for function, count in edge.counts.items():
                if level == 3 and count < 2:
                    continue
                if function in ["__init__", "__getattr__", "__get__", "__str__", "__call__", "<module>"]:
                    continue
                liveNodes.add(fromNode)
                liveNodes.add(toNode)
                if fromNode == toNode:
                    fromNode.selfReference += 1
                calls.append(f"{fromNode.name} => {toNode.name}.{function} called {count} times, total duration: {edge.duration[function]}s")
                edges[(fromNode.index, toNode.index, function)] = {
                    "from": fromNode.index,
                    "to": toNode.index,
                    "label": function,
                    "value": edge.duration[function],
                    "font": {
                        "face": "Courier",
                        "bold": "12pt courier white",
                        "color": "white",
                        "background": "#222",
                        "strokeWidth": 0,
                    },
                    "selfReferenceSize": fromNode.selfReference * 15,
                    "scaling": {
                        "max": 9,
                        "label": {
                            "max": 21,
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
        # print("\n".join(calls))
        js.drawGraph(json.dumps({
            "nodes": [
                {
                    "id": node.index,
                    "label": node.name,
                    "level": node.depth,
                    "shape": "circularImage" if self.getImage(node) else "box",
                    "borderWidth": 2,
                    "value": node.count * 4,
                    "size": 30,
                    "font": { "color": "white" },
                    "image": self.getImage(node),
                    "color": {
                        "border": colors.getColor(node.name, colors.DISCO),
                        "background": "darkgreen" if node.name == "__main__" else colors.getColor(node.name, colors.DISCO),
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
    "runpy": "/microlog/images/icons/python.png",
    "matplotlib": "/microlog/images/icons/matplotlib.png",
    "matplotlib_inline": "/microlog/images/icons/matplotlib.png",
    "squarify": "/microlog/images/icons/squarify.png",
    "pandas": "/microlog/images/icons/pandas.png",
    "numpy": "/microlog/images/icons/numpy.png",
    "asyncio": "/microlog/images/icons/asyncio.png",
    "pyparsing": "/microlog/images/icons/pyparsing.png",
    "ssl": "/microlog/images/icons/ssl.png",
    "http": "/microlog/images/icons/http.png",
    "httplib2": "/microlog/images/icons/http.png",
    "urllib3": "/microlog/images/icons/http.png",
    "socket": "/microlog/images/icons/http.png",
    "pluggy": "/microlog/images/icons/pluggy.webp",
    "pytest": "/microlog/images/icons/pytest.png",
    "testing_tools": "/microlog/images/icons/pytest.png",
    "_pytest": "/microlog/images/icons/pytest.png",
    "networkx": "/microlog/images/icons/networkx.png",
    "re": "/microlog/images/icons/re.png",
    "sre_compile": "/microlog/images/icons/re.png",
    "sre_parse": "/microlog/images/icons/re.png",
    "dataclasses": "/microlog/images/icons/dataclasses.png",
    "tornado": "/microlog/images/icons/tornado.png",
    "urllib": "/microlog/images/icons/urllib.png",
    "guppy": "/microlog/images/icons/guppy.png",
    "zmq": "/microlog/images/icons/zmq.png",
    "email": "/microlog/images/icons/email.png",
    "google_auth_oauthlib": "/microlog/images/icons/google.png",
    "google_auth_httplib2": "/microlog/images/icons/google.png",
    "googleapiclient": "/microlog/images/icons/google.png",
    "google": "/microlog/images/icons/google.png",
    "wsgiref": "/microlog/images/icons/wsgi.png",
    "IPython": "/microlog/images/icons/jupyter.png",
    "jupyter_client": "/microlog/images/icons/jupyter.png",
    "ipykernel": "/microlog/images/icons/jupyter.png",
    "Jupyter": "/microlog/images/icons/jupyter.png",
    "microlog": "/microlog/images/icons/microlog.png",
}