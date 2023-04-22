from __future__ import annotations

import builtins
import js
import json
import pyodide
import traceback

import microlog.stack as stack
import dashboard.canvas as canvas
import microlog.symbols as symbols
import microlog.config as config
import microlog.memory as memory
import microlog.profiler as profiler

from dashboard.dialog import dialog
from dashboard.views import draw
from dashboard.treeview import TreeView
from dashboard.views.call import CallView
from dashboard.views.status import StatusView
from dashboard.views.marker import MarkerView

from typing import List

def print(*args, file=None):
    js.console.log(" ".join(arg if isinstance(arg, str) else repr(arg) for arg in args))

builtins.print = print


class Flamegraph():
    def __init__(self, elementId):
        from dashboard.views import timeline
        self.elementId = elementId
        self.views = []
        self.timeline = timeline.Timeline()
        self.canvas = None
        self.canvas = canvas.Canvas(self.elementId, self.redraw).on("mousemove", self.mousemove)

    @profiler.profile("Flamegraph.load")
    def unmarshall(self, log):
        self.views = []
        self.hover = None
        js.jQuery(self.elementId).empty()
        def parse(line):
            line = f"[{line}]"
            try:
                return json.loads(line)
            except:
                print("PARSE ERROR", line)
                raise
        events = [
            parse(line)
            for line in log.split("\n")
            if line
        ]
        self.views = []
        for lineno, event in enumerate(events):
            kind = event[0]
            try:
                if kind == config.EVENT_KIND_SYMBOL:
                    symbols.unmarshall(event)
                elif kind == config.EVENT_KIND_CALLSITE:
                    stack.CallSite.unmarshall(event)
                elif kind == config.EVENT_KIND_CALL:
                    self.views.append(CallView(self.canvas, event))
                elif kind == config.EVENT_KIND_STATUS:
                    self.views.append(StatusView(self.canvas, event))
                elif kind in [ config.EVENT_KIND_INFO, config.EVENT_KIND_WARN, config.EVENT_KIND_DEBUG, config.EVENT_KIND_ERROR, ]:
                    self.views.append(MarkerView(self.canvas, event))
            except Exception as e:
                raise ValueError(f"Error on line {lineno}", traceback.format_exc(), json.dumps(event))
        self.redraw()
   
    @profiler.report("Redrawing the whole flame graph.")
    def redraw(self, event=None):
        dialog.hide()
        self.draw()
        debug("Draw", profiler.getTime("Flamegraph.draw"))
        if event:
            self.mousemove(event)

    @profiler.profile("Flamegraph.draw")
    def draw(self):
        self.clear()
        self.hover = None
        draw(self.canvas, self.views, self.timeline)

    def clear(self):
        x, w = self.canvas.absolute(0, self.canvas.width())
        h = self.canvas.height()
        self.canvas.fillRect(x, 0, w, h, "#DDD")

    def mousemove(self, event):
        if self.canvas.isDragging() or not hasattr(event.originalEvent, "offsetX"):
            return
        x, _ = self.canvas.absolute(event.originalEvent.offsetX, 0)
        y = event.originalEvent.offsetY
        def checkViews(views):
            for view in views:
                if view.inside(x, y):
                    if self.hover != view:
                        if self.hover:
                            self.hover.mouseleave(x, y)
                        view.mouseenter(x, y)
                    self.hover = view
                    view.mousemove(x, y)
                    return True
        if not checkViews(view for view in self.views if isinstance(view, MarkerView)):
            if not checkViews(view for view in self.views if not isinstance(view, MarkerView)):
                if self.hover:
                    self.hover.mouseleave(x, y)
                    self.hover = None


def showLog(log):
    server = js.location.hostname
    port = js.location.port
    if not "Electron" in js.navigator.userAgent:
        js.history.pushState(js.object(), "", f"http://{server}:{port}/log/{log}")
    loadLog(log)


def loadLog(name):
    url = f"http://127.0.0.1:4000/zip/{name}"
    js.jQuery.get(url, pyodide.ffi.create_proxy(lambda data, status, xhr: showFlamegraph(data)))


@profiler.profile("Logs.show")
def showAllLogs():
    dialog.hide()
    url = "http://127.0.0.1:4000/logs"
    js.jQuery.get(url, pyodide.ffi.create_proxy(lambda data, status, xhr: renderLogs(data.split("\n"))))
    js.jQuery(".logs").css("height", js.jQuery(js.window).height())


def renderLogs(logList: List[str]):
    from collections import defaultdict
    def tree():
        return defaultdict(tree)
    logs = tree()
    for log in [log for log in reversed(logList) if log]:
        application, version, name = log.split("/")
        logs[application][version][name.replace(".log", "")]
    TreeView(js.jQuery(".logs").empty(), logs, lambda name: showLog(name))


flamegraph = Flamegraph("#flamegraph")


def showFlamegraph(log):
    debug("-" * 30)
    debug("Load", profiler.getTime("Flamegraph.load"))
    debug("Size", memory.toGB(len(log)))
    flamegraph.unmarshall(log)


def debug(label: str, value=None) -> None:
    if value == None:
        message = label
    else:
        val = f"{value:.2f}" if isinstance(value, float) else value
        message = f"{label}: {val}<br>"
    js.jQuery("#debug").html(message + js.jQuery("#debug").html())


@profiler.report("Loading the profile data.")
async def main():
    showAllLogs()
    debug("Logs", profiler.getTime("Logs.show"))
    path = js.document.location.pathname
    if path.startswith("/log/"):
        name = path[len("/log/"):]
        loadLog(name)

main()