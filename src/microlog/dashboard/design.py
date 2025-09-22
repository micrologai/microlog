#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Drawing a call graph design for Microlog dashboard."""

from __future__ import annotations

import json

import ltk

import js
from microlog.dashboard import colors
from microlog.dashboard.views.call import CallView

class Node:
    """A node in the call graph representing a module or class."""

    def __init__(self) -> None:
        """Initialize a Node with default values."""
        self.index: int = -1
        self.depth: int = -1
        self.count: int = 1
        self.self_reference: int = 0
        self.module_name: str = ""
        self.class_name: str = ""
        self.name: str = ""

    def set_name(self, module_name: str, class_name: str) -> "Node":
        """Set the module and class name for the node."""
        self.module_name = module_name
        self.class_name = class_name
        self.name = f"{module_name}.{class_name}" if class_name else module_name
        return self

    def set_index(self, index: int) -> "Node":
        """Set the index for the node if not already set."""
        if self.index == -1:
            self.index = index
        return self

    def set_depth(self, depth: int) -> "Node":
        """Set the depth for the node."""
        self.depth = depth
        return self

    def __hash__(self) -> int:
        """Return the hash of the node based on its name."""
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        """Check equality with another node based on name."""
        return isinstance(other, Node) and other.name == self.name


class Edge:
    """An edge in the call graph representing a connection between nodes."""

    def __init__(self) -> None:
        """Initialize an Edge with empty counts and duration."""
        self.counts: dict[str, int] = {}
        self.duration: dict[str, float] = {}
        self.from_node: Node = None
        self.to_node: Node = None

    def connect(
        self, from_node: Node, to_node: Node, function: str, duration: float
    ) -> "Edge":
        """Connect two nodes with a function and accumulate duration/count."""
        self.from_node = from_node
        self.to_node = to_node
        self.counts[function] = self.counts.get(function, 0) + 1
        self.duration[function] = self.duration.get(function, 0) + duration
        return self

    def __repr__(self) -> str:
        """Return a string representation of the edge."""
        return f"{self.from_node.name} => {self.to_node.name}"

    def __hash__(self) -> int:
        """Return the hash of the edge based on its string representation."""
        return self.__repr__().__hash__()

    def __eq__(self, other: object) -> bool:
        """Check equality with another edge based on string representation."""
        return isinstance(other, Edge) and other.__repr__() == self.__repr__()


class Design:
    """Class for drawing and managing the call graph design."""

    LEVEL1: int = 0
    LEVEL2: int = 50
    LEVEL3: int = 100

    def __init__(self, calls: list[CallView]) -> None:
        """Initialize the Design with a list of calls."""
        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, Edge] = {}
        self.calls: list[CallView] = []
        for call in calls:
            self.add_call(call)
        ltk.schedule(self.draw, "draw design")

    def get_node(self, name: str, depth: int) -> Node:
        """Get or create a node by name and depth."""
        parts = name.split(".")
        cls = parts[-2]
        module = ".".join(parts[:-2])
        key = f"{module}.{cls}"
        if key not in self.nodes:
            self.nodes[key] = Node()
        return (
            self.nodes[key]
            .set_name(module, cls)
            .set_index(len(self.nodes))
            .set_depth(depth)
        )

    def get_edge(
        self,
        from_node: Node | None,
        to_node: Node | None,
        function: str,
        duration: float,
    ) -> Edge | None:
        """Get or create an edge between two nodes for a function call."""
        if not from_node or not to_node:
            return None
        key = f"{from_node.name}=>{to_node.name}"
        if key not in self.edges:
            self.edges[key] = Edge()
        return self.edges[key].connect(from_node, to_node, function, duration)

    def add_call(self, call: CallView) -> None:
        """Add a call to the design and update nodes/edges."""
        self.calls.append(call)
        from_node = self.get_node(call.caller_site.name, call.depth)
        to_node = self.get_node(call.call_site.name, call.depth)
        function = call.get_short_name()
        self.get_edge(from_node, to_node, function, call.duration)

    def draw(self) -> None:
        """Draw the call graph using the collected nodes and edges."""
        nodes: dict[str, Node] = {}
        edges = {}
        edge_count = len(self.edges)
        level = 3 if edge_count > self.LEVEL3 else 2 if edge_count > self.LEVEL2 else 1

        def cluster(node: Node) -> Node:
            """Cluster nodes based on the current level of detail."""
            if level == 1:
                name, cls = node.name, node.class_name
            elif level == 2:
                name, cls = ".".join(node.name.split(".")[:-1]), ""
            else:
                name, cls = ".".join(node.name.split(".")[:2]), ""
            if name in nodes:
                node = nodes[name]
                node.count += 1
                return node
            node = Node()
            node.set_name(name, cls).set_index(len(nodes))
            node.self_reference = 0
            nodes[name] = node
            return node

        live_nodes = set()
        calls = []
        for edge in reversed(list(self.edges.values())):
            from_node = cluster(edge.from_node)
            to_node = cluster(edge.to_node)
            if from_node == to_node and level > 1:
                continue
            for function, count in edge.counts.items():
                if level == 3 and count < 2:
                    continue
                if function in [
                    "__init__",
                    "__getattr__",
                    "__get__",
                    "__str__",
                    "__call__",
                    "<module>",
                ]:
                    continue
                live_nodes.add(from_node)
                live_nodes.add(to_node)
                if from_node == to_node:
                    from_node.self_reference += 1
                calls.append(
                    f"{from_node.name} => {to_node.name}.{function} called {count} times, "
                    f"total duration: {edge.duration[function]}s"
                )
                edges[(from_node.index, to_node.index, function)] = {
                    "from": from_node.index,
                    "to": to_node.index,
                    "label": f"{function} {edge.duration[function]:.1f}s",
                    "value": edge.duration[function] * 17,
                    "font": {
                        "face": "Courier",
                        "bold": "12pt courier white",
                        "color": "white",
                        "background": "#222",
                        "strokeWidth": 0,
                    },
                    "selfReferenceSize": from_node.self_reference * 15,
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
        js.draw_graph(
            json.dumps(
                {
                    "nodes": [
                        {
                            "id": node.index,
                            "label": node.name,
                            "level": node.depth,
                            "shape": "circularImage" if self.get_image(node) else "box",
                            "borderWidth": 2,
                            "value": node.count * 4,
                            "size": 30,
                            "font": {"color": "black"},
                            "image": self.get_image(node),
                            "color": {
                                "border": colors.get_color(node.name, colors.PASTEL),
                                "background": "white"
                                if node.name == "__main__"
                                else colors.get_color(node.name, colors.PASTEL),
                                "highlight": {
                                    "border": "red",
                                    "background": "white",
                                },
                                "hover": {"border": "orange", "background": "grey"},
                            },
                            "imagePadding": {
                                "left": 2,
                                "top": 2,
                                "right": 2,
                                "bottom": 8,
                            },
                        }
                        for node in live_nodes
                    ],
                    "edges": list(edges.values()),
                }
            )
        )

    def get_image(self, _: Node) -> str | None:
        """Get the image associated with a node, if any."""
        return ""
