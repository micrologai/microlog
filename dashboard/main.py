#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import builtins
import js # type: ignore
import json
import pyodide # type: ignore
import traceback

import dashboard.canvas as canvas
import microlog.config as config
import microlog.models as models
import dashboard.profiler as profiler

from dashboard.dialog import dialog
from dashboard.views import draw
from dashboard.treeview import TreeView
from dashboard.views.call import CallView
from dashboard.views.status import StatusView
from dashboard.views.marker import MarkerView
from dashboard.design import Design

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
        self.design = Design()
        self.canvas = (
            canvas.Canvas(self.elementId, self.redraw)
                .on("mousemove", self.mousemove)
                .on("click", self.click)
        )
        js.jQuery(".tabs").on("tabsactivate", pyodide.ffi.create_proxy(lambda event, ui: self.activateTab(event)))

    def activateTab(self, event):
        print("activate tab", event)
        self.redraw()

    @profiler.profile("Flamegraph.load")
    def unmarshall(self, log):
        self.views = []
        self.design = Design()
        self.hover = None
        js.jQuery(self.elementId).empty()
        js.jQuery("#tabs-log").find("table").empty()
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
            print("  ", event, ", #", config.kinds[event[0]])
            try:
                if kind == config.EVENT_KIND_SYMBOL:
                    models.unmarshallSymbol(event)
                elif kind == config.EVENT_KIND_CALLSITE:
                    models.CallSite.unmarshall(event)
                elif kind == config.EVENT_KIND_CALL:
                    callView = CallView(self.canvas, event)
                    self.views.append(callView)
                    self.design.addCall(callView)
                elif kind == config.EVENT_KIND_META:
                    self.meta = models.Meta.unmarshall(event)
                    self.design.setMeta(self.meta)
                    self.addLogEntry(self.meta.when, self.meta.message, self.meta.stack)
                elif kind == config.EVENT_KIND_STATUS:
                    self.views.append(StatusView(self.canvas, event))
                elif kind in [ config.EVENT_KIND_INFO, config.EVENT_KIND_WARN, config.EVENT_KIND_DEBUG, config.EVENT_KIND_ERROR, ]:
                    marker = MarkerView(self.canvas, event)
                    self.addLogEntry(marker.when, marker.toHTML(marker.message), marker.formatStack(full=False))
                    self.views.append(marker)
            except Exception as e:
                print(f"Error on line {lineno} of recording<br><br>{traceback.format_exc()}<br><br>{json.dumps(event)}")
        self.redraw()
   
    @profiler.report("Redrawing the whole flame graph.")
    def redraw(self, event=None):
        self.draw()
        self.design.draw()
        debug("Draw", profiler.getTime("Flamegraph.draw"))
        if event:
            self.mousemove(event) 

    @profiler.report("Adding log entry.")
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
        self.clear()
        self.hover = None
        draw(self.canvas, self.views, self.timeline)

    def clear(self):
        self.canvas.clear("#DDD")
        CallView.clear()

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
        if not checkViews(view for view in self.views if isinstance(view, MarkerView)):
            if not checkViews(view for view in self.views if not isinstance(view, MarkerView)):
                if self.hover:
                    self.hover.mouseleave(x, y)
                    self.hover = None

    def click(self, event):
        if self.canvas.isDragging() or not hasattr(event.originalEvent, "offsetX"):
            return
        x, _ = self.canvas.absolute(event.originalEvent.offsetX, 0)
        y = event.originalEvent.offsetY
        for view in self.views:
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
    setUrl(log)
    loadLog(log)


def loadLog(name):
    url = f"http://127.0.0.1:4000/zip/{name}"
    js.jQuery.get(url, pyodide.ffi.create_proxy(lambda data, status, xhr: showFlamegraph(data)))


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


def showFlamegraph(log):
    js.jQuery("#debug").html("")
    debug("Load", profiler.getTime("Flamegraph.load"))
    debug("Size", models.toGB(len(log)))
    flamegraph.unmarshall(log)


def debug(label: str, value=None) -> None:
    if value == None:
        message = label
    else:
        val = f"{value:.2f}" if isinstance(value, float) else value
        message = f"{label}: {val}<br>"
    js.jQuery("#debug").html(message + js.jQuery("#debug").html())
    

def refreshLogs(event=None):
    js.setTimeout(pyodide.ffi.create_proxy(lambda: showAllLogs()), 1)


def setupLogHandlers():
    js.jQuery(".refresh").click(pyodide.ffi.create_proxy(refreshLogs))
    js.jQuery(".filter").keyup(pyodide.ffi.create_proxy(refreshLogs))


@profiler.report("Loading the profile data.")
async def main():
    setupLogHandlers()
    showAllLogs()
    loadLog(getLogFromUrl())
    debug("Logs", profiler.getTime("Logs.show"))

main()