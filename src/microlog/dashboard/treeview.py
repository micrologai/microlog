#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#
"""Tree view component for displaying hierarchical data."""

from __future__ import annotations

from typing import Any
from typing import Callable

import ltk
import js


TOGGLE_OPEN = "<div class='tree-toggle'>▽</div>"
TOGGLE_CLOSED = "<div class='tree-toggle'>▷</div>"


class TreeView:
    """Tree view component for displaying hierarchical data."""
    instance: TreeView | None = None

    def __init__(
        self,
        parent: Any,
        items: dict[str, Any],
        selected: str,
        selection_handler: Callable[[str], None],
        delete_handler: Callable[[str, Callable[[], None]], None],
        reload_handler: Callable[[], None],
    ) -> None:
        self.selection_handler: Callable[[str], None] = selection_handler
        self.delete_handler: Callable[[str, Callable[[], None]], None] = delete_handler
        self.reload_handler: Callable[[], None] = reload_handler
        self.parent: Any = parent
        TreeView.instance = self

        def add(
            parent: Any, path: list[str], items: dict[str, Any], depth: int = 0
        ) -> None:
            ul = (
                js.jQuery("<div>")
                .addClass("tree-indent" if depth else "tree")
                .appendTo(parent)
            )

            def delete(event: Any) -> None:
                event.preventDefault()
                event.stopPropagation()
                node = js.jQuery(event.target).parent()
                self.delete(node)

            for label in sorted(items.keys(), reverse=True):
                children = items[label]
                is_leaf = len(children) == 0
                node = js.jQuery("<div>").addClass("tree-node").appendTo(ul)
                full_path = f"{'/'.join(path)}/{label}"
                stored_toggle = js.localStorage.getItem(f"tree-toggle-{label}") or "open"
                toggle = TOGGLE_CLOSED if stored_toggle == "closed" else TOGGLE_OPEN
                row = (js.jQuery("<div>")
                    .addClass("tree-row")
                    .css("padding-left", 1 + depth * 14)
                    .attr("path", "/".join(path))
                    .attr("label", label)
                    .attr("children", len(children))
                    .addClass("tree-not-leaf" if children else "tree-leaf")
                    .addClass(
                        "tree-selected" if full_path == selected else "tree-not-selected"
                    )
                    .attr("index", js.jQuery(".tree-leaf").length if is_leaf else -1)
                    .click(
                        ltk.proxy(
                            lambda event: self.click(
                                js.jQuery(event.target).closest(".tree-row")
                            )
                        )
                    )
                    .append(
                        js.jQuery("<span>")
                        .addClass("tree-label")
                        .html(f"{toggle} {label}" if not is_leaf else f"  {label}"),
                        js.jQuery("<span>")
                        .addClass("tree-delete-icon")
                        .html("❌")
                        .click(ltk.proxy(delete)),
                    )
                )
                if toggle == TOGGLE_CLOSED:
                    node.addClass("closed" if toggle == TOGGLE_CLOSED else "")
                node.append(row)
                add(
                    js.jQuery("<div>").appendTo(node),
                    path + [label],
                    children,
                    depth + 1,
                )

        add(parent, [], items)
        self.scroll_into_view(js.jQuery(".tree-selected"))

    def key_down(self, event: Any) -> None:
        """Handle key down events for navigation."""
        if event.keyCode in [38, 40]:
            index = int(js.jQuery(".tree-selected").attr("index")) or 0
            direction = -1 if event.keyCode == 38 else 1
            index += direction
            selected = js.jQuery(f".tree-leaf[index='{index}']")
            if index >= 0 and selected.length:
                self.select_node(selected)
            event.preventDefault()

    def delete_leaf(self, leaf: Any) -> None:
        """Delete a leaf node from the tree view."""
        self.delete_handler(
            f"{leaf.attr('path')}/{leaf.attr('label')}", lambda: leaf.remove() # pylint: disable=unnecessary-lambda
        )

    def delete(self, node: Any) -> None:
        """Delete a node and its children from the tree view."""
        leaves = node.parent().find(".tree-leaf")
        for index in range(leaves.length):
            self.delete_leaf(leaves.eq(index))
        node.parent().remove()

    def open_node(self, node: Any) -> None:
        """Open a tree node to show its children."""
        node.closest(".tree-node").removeClass("closed")
        node.find(".tree-label").html(f"{TOGGLE_OPEN} {node.attr('label')}")
        js.localStorage.setItem(f"tree-toggle-{node.attr('label')}", "open")

    def close_node(self, node: Any) -> None:
        """Close a tree node to hide its children."""
        node.closest(".tree-node").addClass("closed")
        node.find(".tree-label").html(f"{TOGGLE_CLOSED} {node.attr('label')}")
        js.localStorage.setItem(f"tree-toggle-{node.attr('label')}", "closed")

    def click(self, node: Any) -> None:
        """Handle click events on tree nodes."""
        if int(node.attr("children")):
            print("open/close", node.text())
            if node.closest(".tree-node").hasClass("closed"):
                self.open_node(node)
            else:
                self.close_node(node)
        else:
            self.select_node(node)

    def select_node(self, node: Any) -> None:
        """Select a tree node and notify the selection handler."""
        js.jQuery(".tree-selected").removeClass("tree-selected")
        node.addClass("tree-selected")
        self.selection_handler(f"{node.attr('path')}/{node.attr('label')}")
        self.scroll_into_view(node)

    def scroll_into_view(self, node: Any) -> None:
        """Scroll the selected node into view if it's not already visible."""
        if not node.isInViewport():
            node[0].scrollIntoView()


js.jQuery("body").on(
    "keydown",
    ltk.proxy(
        lambda event: TreeView.instance.key_down(event) if TreeView.instance else None
    ),
)
