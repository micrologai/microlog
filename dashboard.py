from __future__ import annotations

import builtins
import js
import json
import pyodide
import traceback

import microlog.stack as stack
import microlog.dashboard.canvas as canvas
import microlog.symbols as symbols
import microlog.config as config
import microlog.profiler as profiler

from microlog.dashboard.dialog import dialog
from microlog.dashboard.views import draw
from microlog.dashboard.views.call import CallView
from microlog.dashboard.views.status import StatusView
from microlog.dashboard.views.span import SpanView
from microlog.dashboard.views.marker import MarkerView


def print(*args):
    js.console.log(" ".join(arg if isinstance(arg, str) else repr(arg) for arg in args))

builtins.print = print


class Flamegraph():
    def __init__(self, elementId):
        self.elementId = elementId

    @profiler.profile("Flamegraph.load")
    def load(self, log):
        self.views = []
        self.hover = None
        js.jQuery(self.elementId).empty()
        self.canvas = canvas.Canvas(self.elementId, self.redraw).on("mousemove", self.mousemove)
        from microlog.dashboard.views import timeline
        self.timeline = timeline.Timeline()
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
                    symbols.load(event)
                elif kind == config.EVENT_KIND_CALLSITE:
                    stack.CallSite.load(event)
                elif kind == config.EVENT_KIND_CALL:
                    self.views.append(CallView(self.canvas, event))
                elif kind == config.EVENT_KIND_STATUS:
                    self.views.append(StatusView(self.canvas, event))
                elif kind in [ config.EVENT_KIND_INFO, config.EVENT_KIND_WARN, config.EVENT_KIND_DEBUG, config.EVENT_KIND_ERROR, ]:
                    self.views.append(MarkerView(self.canvas, event))
                elif kind == config.EVENT_KIND_SPAN:
                    self.views.append(SpanView(self.canvas, event))
            except Exception as e:
                raise ValueError(f"Error on line {lineno}", traceback.format_exc(), json.dumps(event))
   
    @profiler.report("Redrawing the whole flame graph.")
    def redraw(self, event=None):
        dialog.hide()
        self.draw()
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
        self.canvas.rect(x, 0, w, h, "#DDD", 1, "white")

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
    print("showLog", log)
    js.history.pushState(js.object(), "", f"http://127.0.0.1:4000/log/{log}")
    loadLog(log)


def loadLog(name):
    print("loadLog", name)
    url = f"http://127.0.0.1:4000/zip/{name}"
    js.jQuery.get(url, pyodide.ffi.create_proxy(lambda data, status, xhr: showFlamegraph(data)))


def createChoice(log):
    return js.jQuery("<li>").append(js.jQuery("<span>") \
        .addClass("log") \
        .attr("log", f"/log/{log}") \
        .click(pyodide.ffi.create_proxy(lambda event: showLog(log))) \
        .text(log))


def showAllLogs():
    dialog.hide()
    url = "http://127.0.0.1:4000/logs"
    js.jQuery.get(url, pyodide.ffi.create_proxy(lambda data, status, xhr: renderLogs(data)))


def renderLogs(logs):
    js.jQuery(".dashboard").css("visibility", "hidden")
    js.jQuery(".logs").css("visibility", "visible")
    from collections import defaultdict
    logsByApplication = defaultdict(list)
    for log in reversed([log for log in logs.split("\n") if log]):
        logsByApplication[log.split("-")[0]].append(log)
    js.jQuery(".logs").empty()
    for application, logs in logsByApplication.items():
        label = js.jQuery("<div>").text(application)
        ul = js.jQuery("<ul>")
        js.jQuery(".logs").append(label, ul)
        for log in logs:
            ul.append(createChoice(log))

flamegraph = Flamegraph("#flamegraph")

def showFlamegraph(log):
    js.jQuery(".logs").css("visibility", "hidden")
    js.jQuery(".dashboard").css("visibility", "visible")
    js.jQuery(".flamegraph-container") \
        .empty() \
        .append(js.jQuery("<canvas>") \
            .attr("id", "flamegraph"))
    flamegraph.load(log)


@profiler.report("Loading the profile data.")
async def main():
    path = js.document.location.pathname
    print("MAIN", path)
    if path == "/": 
        showAllLogs()
    else:
        name = path[len("/log/"):]
        loadLog(name)

js.addEventListener("popstate", pyodide.ffi.create_proxy(lambda event: showAllLogs()))

main()