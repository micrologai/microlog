#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import builtins
import js # type: ignore
import pyodide # type: ignore

from dashboard import canvas
from microlog import log
from dashboard import profiler

from dashboard.dialog import dialog
from dashboard.treeview import TreeView
from dashboard.views.call import CallView
from dashboard.views.status import StatusView
from dashboard.views.marker import MarkerView
from dashboard.design import Design
from dashboard import markdown

from typing import List

def print(*args, file=None, **argv):
    js.console.log(" ".join(arg if isinstance(arg, str) else repr(arg) for arg in args))

builtins.print = print


class Flamegraph():
    def __init__(self, elementId):
        from dashboard.views import timeline
        self.elementId = elementId
        self.timeline = timeline.Timeline()
        self.design = Design([])
        self.currentTab = "Profiler"
        self.hover = None
        self.canvas = (
            canvas.Canvas(self.elementId, self.redraw)
                .on("mousemove", self.mousemove)
                .on("click", self.click)
        )
        js.jQuery(".tabs").on("tabsactivate", pyodide.ffi.create_proxy(lambda event, ui: self.activateTab(event, ui)))

    def activateTab(self, event, ui):
        self.currentTab = ui.newTab.text()
        self.redraw()

    def reset(self):
        self.canvas.reset()

    @profiler.profile("Flamegraph.load")
    def load(self, log):
        self.calls = [ CallView(self.canvas, model) for model in log.log.calls ]
        self.statuses = [ StatusView(self.canvas, model) for model in log.log.statuses ]
        self.markers = [ MarkerView(self.canvas, model) for model in log.log.markers ]
        self.design = Design(self.calls)
        js.jQuery("#tabs-log").find("table").empty()
        for marker in self.markers:
            self.addLogEntry(marker.when, markdown.toHTML(marker.message), marker.formatStack(full=False))
        self.hover = None
        js.jQuery(self.elementId).empty()
        self.redraw()
   
    @profiler.report("Redrawing the whole flame graph.")
    def redraw(self, event=None):
        if self.currentTab == "Profiler":
            self.draw()
            debug("Draw", profiler.getTime("Flamegraph.draw"))
        elif self.currentTab == "Design":
            js.jQuery("#debug").html("")
            self.design.draw()
        elif self.currentTab == "Explanation":
            explain(getLogFromUrl())
        if event:
            self.mousemove(event) 

    @profiler.profile("Adding log entry.")
    def addLogEntry(self, when, entry, stack):
        js.jQuery("#tabs-log").find("table").append(
            js.jQuery("<tr>").append(
                js.jQuery("<td>").addClass("log-when").append(
                    js.jQuery("<div>").html(f"At&nbsp;{when:.2f}s")
                ),
                js.jQuery("<td>").addClass("log-stack").append(
                    js.jQuery("<div>").html(stack)
                ),
                js.jQuery("<td>").addClass("log-message").append(
                    js.jQuery("<pre>").html(entry)
                ),
            )
        )

    @profiler.profile("Flamegraph.draw")
    def draw(self):
        self.canvas.clear("#DDD")
        self.hover = None
        StatusView.drawAll(self.canvas, [view for view in self.statuses if not view.offscreen()])
        CallView.drawAll(self.canvas, [view for view in self.calls if not view.offscreen()])
        MarkerView.drawAll(self.canvas, [view for view in self.markers if not view.offscreen()])
        self.timeline.draw(self.canvas)

    def mousemove(self, event):
        if self.canvas.isDragging() or not hasattr(event.originalEvent, "offsetX"):
            return
        x, _ = self.canvas.absolute(event.originalEvent.offsetX, 0)
        y = event.originalEvent.offsetY
        def checkViews(views):
            for view in views:
                if view.inside(x, y):
                    if not self.hover is view:
                        if self.hover:
                            self.hover.mouseleave(x, y)
                        view.mouseenter(x, y)
                    self.hover = view
                    view.mousemove(x, y)
                    return True
        if not checkViews(view for view in self.markers):
            if self.hover:
                self.hover.mouseleave(x, y)
                self.hover = None

    def click(self, event):
        if self.canvas.isDragging() or not hasattr(event.originalEvent, "offsetX"):
            return
        x, _ = self.canvas.absolute(event.originalEvent.offsetX, 0)
        y = event.originalEvent.offsetY
        self.checkClick(self.markers, x, y)
        self.checkClick(self.calls, x, y)

    def checkClick(self, views, x, y):
        for view in views:
            if view.inside(x, y):
                view.click(x, y)
                return True


def setUrl(log=None):
    if not "Electron" in js.navigator.userAgent:
        server = js.location.hostname
        port = js.location.port
        filter = js.jQuery(".filter").val()
        if log:
            url = f"http://{server}:{port}/log/{log}?filter={filter}"
        else:
            url = f"http://{server}:{port}/?filter={filter}"
        js.history.pushState(js.object(), "", url)


def showLog(log):
    dialog.hide()
    CallView.reset()
    loadLog(log)
    if log.split("/")[:2] != getLogFromUrl().split("/")[:2]:
        flamegraph.reset()
    setUrl(log)
    js.jQuery("#explanation").text("")


def loadLog(name):
    url = f"http://127.0.0.1:4000/zip/{name}"
    js.jQuery.get(url, pyodide.ffi.create_proxy(lambda data, status, xhr: showFlamegraph(data)))


def explain(name):
    if not js.jQuery("#explanation").text():
        js.jQuery("#explanation").text("Asking OpenAI to explain this program...")
        url = f"http://127.0.0.1:4000/explain/{name}"
        js.jQuery.get(url, pyodide.ffi.create_proxy(lambda data, status, xhr: js.jQuery("#explanation").html(markdown.toHTML(data))))


@profiler.profile("Logs.show")
def showAllLogs():
    dialog.hide()
    filter = js.jQuery(".filter").val()
    url = f"http://127.0.0.1:4000/logs?filter={filter}"
    js.jQuery.get(url, pyodide.ffi.create_proxy(lambda data, status, xhr: renderLogs(data.strip().split("\n"))))
    js.jQuery(".logs") \
        .css("height", js.jQuery(js.window).height()) \
        .empty() \
        .append(js.jQuery("<img>").addClass("loading").attr("src", "/images/spinner.gif"))


def deleteLog(name, doneHandler):
    url = f"http://127.0.0.1:4000/delete/{name}"
    js.jQuery.get(url, pyodide.ffi.create_proxy(lambda data, status, xhr: doneHandler()))


def getLogFromUrl():
    path = js.document.location.pathname
    if path.startswith("/log/"):
        return path[len("/log/"):]


def renderLogs(logList: List[str]):
    from collections import defaultdict
    if not any(logList):
        js.jQuery(".logs").empty().append(js.jQuery("<span>").css("color", "pink").text("No matching logs found")),
        return
    def tree():
        return defaultdict(tree)
    logs = tree()
    for log in [log for log in reversed(logList) if log]:
        application, version, name = log.split("/")
        if application != "-":
            logs[application][version][name.replace(".log", "")]
    TreeView(
        js.jQuery(".logs").empty(),
        logs,
        getLogFromUrl(),
        lambda path: showLog(path),
        lambda path, doneHandler: deleteLog(path, doneHandler),
        refreshLogs
    )


flamegraph = Flamegraph("#flamegraph")


def showFlamegraph(data):
    log.log.load(data)
    js.jQuery("#debug").html("")
    debug("Load", profiler.getTime("Flamegraph.load"))
    flamegraph.load(log)


def debug(label: str, value=None) -> None:
    if value == None:
        message = label
    else:
        val = f"{value:.3f}" if isinstance(value, float) else value
        message = f"{label}: {val}<br>"
    js.jQuery("#debug").html(message + js.jQuery("#debug").html())
    

def refreshLogs(event=None):
    js.setTimeout(pyodide.ffi.create_proxy(lambda: showAllLogs()), 1)


def setupLogHandlers():
    js.jQuery(".refresh").click(pyodide.ffi.create_proxy(refreshLogs))
    js.jQuery(".filter").keyup(pyodide.ffi.create_proxy(refreshLogs))


def main():
    setupLogHandlers()
    showAllLogs()
    loadLog(getLogFromUrl())
    debug("Logs", profiler.getTime("Logs.show"))

main()