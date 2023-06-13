#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import builtins
import js # type: ignore
import json
import pyodide # type: ignore
import traceback

from typing import List


class TreeView():
    instance = None

    def __init__(self, parent, items: dict, selected, selectionHandler, deleteHandler, reloadHandler):
        self.selectionHandler = selectionHandler
        self.deleteHandler = deleteHandler
        self.reloadHandler = reloadHandler
        self.parent = parent
        TreeView.instance = self

        def add(parent, path: List[str], items, depth=0):
            ul = js.jQuery("<div>") \
                .addClass("tree-indent" if depth else "tree") \
                .appendTo(parent)
            for label, children in items.items():
                isLeaf = len(children) == 0
                node = js.jQuery("<div>").addClass("tree-node").appendTo(ul)
                fullPath =  f"{'/'.join(path)}/{label}"
                node.append(js.jQuery("<div>") \
                    .addClass("tree-row") \
                    .css("padding-left", depth * 12) \
                    .attr("path", "/".join(path)) \
                    .attr("label", label) \
                    .attr("children", len(children)) \
                    .addClass("tree-not-leaf" if children else "tree-leaf") \
                    .addClass("tree-selected" if fullPath == selected else "tree-not-selected") \
                    .attr("index", len(js.jQuery(".tree-leaf")) if isLeaf else -1) \
                    .click(pyodide.ffi.create_proxy(lambda event: self.click(js.jQuery(event.target).closest(".tree-row")))) \
                    .append(
                        js.jQuery("<span>") \
                            .addClass("tree-label") \
                            .html(f"▶ {label}" if not isLeaf else f"  {label}"), \
                        js.jQuery("<span>") \
                            .addClass("tree-delete-icon") \
                            .html(f"🗑") \
                            .click(pyodide.ffi.create_proxy(lambda event: self.delete(js.jQuery(event.target).parent()))) 
                    )
                )
                add(js.jQuery("<div>").appendTo(node), path + [label], children, depth+1)
        add(parent, [], items)

    def keyDown(self, event):
        if event.keyCode in [38, 40]: 
            index = int(js.jQuery(".tree-selected").attr("index")) or 0
            direction = -1 if event.keyCode == 38 else 1
            index += direction
            selected = js.jQuery(f".tree-leaf[index='{index}']")
            if index >= 0 and selected.length:
                self.selectNode(selected)
            event.preventDefault()

    def delete(self, node):
        if node.hasClass("tree-leaf"):
            self.deleteHandler(f"{node.attr('path')}/{node.attr('label')}", lambda: node.remove())
            node.remove()
        else:
            def deleteLeaf(index, element):
                node = js.jQuery(element)
                self.deleteHandler(f"{node.attr('path')}/{node.attr('label')}", lambda: node.remove())
            node.parent().find(".tree-leaf").each(pyodide.ffi.create_proxy(deleteLeaf))
        self.reloadHandler()

    def openNode(self, node):
        node.removeClass("closed").addClass("open")
        node.find(".tree-label").text(f"▼ {node.attr('label')}")
        node.parent().css("height", "")

    def closeNode(self, node):
        node.removeClass("open").addClass("closed")
        node.find(".tree-label").text(f"▶ {node.attr('label')}")
        node.parent().css("height", node.height() + 3)

    def click(self, node):
        if int(node.attr("children")):
            if node.hasClass("closed"):
                self.openNode(node)
            else:
                self.closeNode(node)
        else:
            self.selectNode(node)
        

    def selectNode(self, node):
        js.jQuery(".tree-selected").removeClass("tree-selected")
        node.addClass("tree-selected")
        self.selectionHandler(f"{node.attr('path')}/{node.attr('label')}")
    

js.jQuery("body").on("keydown", pyodide.ffi.create_proxy(lambda event: TreeView.instance.keyDown(event)))