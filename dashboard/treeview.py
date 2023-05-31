from __future__ import annotations

import builtins
import js
import json
import pyodide
import traceback

from typing import List


class TreeView():
    def __init__(self, parent, items: dict, selectionHandler, deleteHandler):
        self.selectionHandler = selectionHandler
        self.deleteHandler = deleteHandler
        self.parent = parent
        self.index = 0

        def add(parent, path: List[str], items, depth=0):
            ul = js.jQuery("<div>") \
                .addClass("tree-indent" if depth else "tree") \
                .appendTo(parent)
            for label, children in items.items():
                isLeaf = len(children) == 0
                node = js.jQuery("<div>").addClass("tree-node").appendTo(ul)
                node.append(js.jQuery("<div>") \
                    .addClass("tree-row") \
                    .css("padding-left", depth * 12) \
                    .attr("path", "/".join(path)) \
                    .attr("label", label) \
                    .attr("children", len(children)) \
                    .addClass("tree-not-leaf" if children else "tree-leaf") \
                    .append(
                        js.jQuery("<span>") \
                            .addClass("tree-label") \
                            .attr("index", self.index if isLeaf else -1) \
                            .html(f"▼ {label}" if not isLeaf else f"  {label}") \
                            .click(pyodide.ffi.create_proxy(lambda event: self.click(js.jQuery(event.target).parent()))), \
                        js.jQuery("<span>") \
                            .addClass("tree-delete-icon") \
                            .html(f"🗑") \
                            .click(pyodide.ffi.create_proxy(lambda event: self.delete(js.jQuery(event.target).parent()))) 
                    )
                )
                add(js.jQuery("<div>").appendTo(node), path + [label], children, depth+1)
                if isLeaf:
                    self.index += 1
        add(parent, [], items)
        js.jQuery("body").on("keydown", pyodide.ffi.create_proxy(lambda event: self.keyDown(event)))

    def keyDown(self, event):
        if event.keyCode in [38, 40]: 
            index = int(js.jQuery(".tree-selected").attr("index")) or 0
            direction = -1 if event.keyCode == 38 else 1
            index += direction
            selected = js.jQuery(f".tree-label[index='{index}']")
            if index >= 0 and selected.length:
                self.selectNode(selected)
            event.preventDefault()

    def delete(self, node):
        if node.hasClass("tree-leaf"):
            self.deleteHandler(f"{node.attr('path')}/{node.attr('label')}")
            node.remove()
        else:
            def deleteLeaf(index, element):
                node = js.jQuery(element)
                self.deleteHandler(f"{node.attr('path')}/{node.attr('label')}", lambda: node.remove())
            node.parent().find(".tree-leaf").each(pyodide.ffi.create_proxy(deleteLeaf))

    def click(self, node):
        if int(node.attr("children")):
            if node.hasClass("closed"):
                node \
                    .removeClass("closed") \
                    .addClass("open") \
                    .text(f"▼ {node.attr('label')}") \
                    .parent().css("height", "")
            else:
                node \
                    .removeClass("open") \
                    .addClass("closed") \
                    .text(f"▶ {node.attr('label')}") \
                    .parent().css("height", node.height() + 3)
        else:
            self.selectNode(node)
    
    def selectNode(self, node):
        js.jQuery(".tree-selected").removeClass("tree-selected")
        node.addClass("tree-selected")
        self.selectionHandler(f"{node.attr('path')}/{node.attr('label')}")