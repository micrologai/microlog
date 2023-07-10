#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

import builtins
import js # type: ignore
import pyodide # type: ignore

from dashboard import canvas
from microlog import log
from dashboard import config
from dashboard import profiler

from dashboard.dialog import dialog
from dashboard.treeview import TreeView
from dashboard.views.call import CallView
from dashboard.views.status import StatusView
from dashboard.views.marker import MarkerView
from dashboard.design import Design
from dashboard.tips import Tips
from dashboard import markdown

from typing import List

def print(*args, file=None, **argv):
    js.console.log(" ".join(arg if isinstance(arg, str) else repr(arg) for arg in args))

builtins.print = print


class Flamegraph():
    def __init__(self, flameElementId, timelineElementId):
        from dashboard.views import timeline
        self.timelineElementId = timelineElementId
        self.flameElementId = flameElementId
        self.timeline = timeline.Timeline()
        self.design = Design([])
        self.currentTab = "Timeline"
        self.hover = None
        self.calls = []
        self.statuses = []
        self.markers = []
        self.design = Design([])
        self.tips = Tips([])
        self.flameCanvas = self.createCanvas(self.flameElementId, self.clickFlame, self.dragFlame, self.zoomFlame, self.flameMousemove, fixedScaleY=True)
        self.timelineCanvas = self.createCanvas(self.timelineElementId, self.clickTimeline, self.dragTimeline, self.zoomTimeline, self.timelineMousemove, fixedY=True, fixedScaleY=True)
        js.jQuery(".tabs").on("tabsactivate", pyodide.ffi.create_proxy(lambda event, ui: self.activateTab(event, ui)))

    def dragFlame(self, dx, dy):
        self.timelineCanvas.drag(dx, dy)
        CallView.positionThreads(self.flameCanvas)

    def zoomFlame(self, x, y, scale):
        self.timelineCanvas.zoom(x, y, scale)

    def dragTimeline(self, dx, dy):
        self.flameCanvas.drag(dx, dy)

    def zoomTimeline(self, x, y, scale):
        self.flameCanvas.zoom(x, y, scale)

    def resize(self, width, height):
        timelineHeight = config.TIMELINE_OFFSET_Y + config.TIMELINE_HEIGHT 
        self.timelineCanvas.width(width)
        self.timelineCanvas.height(timelineHeight)
        self.flameCanvas.width(width)
        self.flameCanvas.height(height - timelineHeight)
        self.redraw()

    def createCanvas(self, elementId, click, drag, zoom, mousemove, fixedY=False, fixedScaleY=False):
        return (canvas.Canvas(elementId, self.redraw, drag, zoom, minOffsetX=48, minOffsetY=0, fixedY=fixedY, fixedScaleY=fixedScaleY)
            .on("mousemove", mousemove)
            .on("click", click))

    def activateTab(self, event, ui):
        self.currentTab = ui.newTab.text()
        self.redraw()

    def reset(self):
        self.timelineCanvas.reset()
        self.flameCanvas.reset()

    @profiler.report("Flamegraph.load")
    def load(self, log):
        self.calls = [ CallView(self.flameCanvas, model) for model in log.log.calls ]
        self.statuses = [ StatusView(self.timelineCanvas, model) for model in log.log.statuses ]
        self.markers = [ MarkerView(self.timelineCanvas, model) for model in log.log.markers ]
        self.design = Design(self.calls)
        self.tips = Tips(self.calls)
        statusIndex = 0
        logEntries = []
        def showStatus(index):
            if self.statuses and index < len(self.statuses):
                logEntries.append((self.statuses[index].when, str(self.statuses[index]), ""))
        showStatus(0)
        for marker in self.markers:
            while self.statuses[statusIndex].when < marker.when and statusIndex < len(self.statuses) - 1:
                statusIndex += 1
            logEntries.append((marker.when, markdown.toHTML(marker.message), marker.formatStack(full=False)))
            showStatus(statusIndex)
        self.addLogEntries(logEntries)
        showStatus(-1)
        self.hover = None
        js.jQuery(self.flameElementId).empty()
        js.jQuery(self.timelineElementId).empty()
   
    @profiler.report("Redrawing the whole flame graph.")
    def redraw(self, event=None):
        if self.currentTab == "Timeline":
            self.draw()
            debug("Draw", profiler.getTime("Flamegraph.draw"))
        elif self.currentTab == "Design":
            js.jQuery("#debug").html("")
            self.design.draw()
        elif self.currentTab == "Explanation":
            explain(getLogFromUrl())
        if event:
            self.mousemove(event) 

    @profiler.profile("Adding log entries.")
    def addLogEntries(self, logEntries):
        js.jQuery("#tabs-log").html(f"""
            <table>
            {"".join(self.getLogEntry(when, entry, stack) for when, entry, stack in logEntries)}
            </table>
        """)

    @profiler.profile("Adding one log entry.")
    def getLogEntry(self, when, entry, stack):
        def fixNewline(s):
            return s.replace("\n", "<br>")
        return f"""
            <tr>
                <td class="log-when">At&nbsp;{when:.2f}s</td>
                <td class="log-stack">{fixNewline(stack)}</td>
                <td class="log-message">{entry}</td>
            </tr>
        """

    @profiler.profile("Flamegraph.draw")
    def draw(self):
        self.flameCanvas.clear("#DDD")
        self.timelineCanvas.clear("#DDD")
        self.hover = None
        width = self.flameCanvas.width()
        StatusView.drawAll(self.timelineCanvas, [view for view in self.sampleStatuses() if not view.offscreen(width)])
        self.timeline.draw(self.timelineCanvas)
        CallView.drawAll(self.flameCanvas, [view for view in self.calls if not view.offscreen(width)])
        MarkerView.drawAll(self.timelineCanvas, [view for view in self.markers if not view.offscreen(width)])
        
    def sampleStatuses(self):
        if not self.statuses: 
            return []
        statuses = [ self.statuses[0] ]
        sample = int(max(1, 1 / self.flameCanvas.scaleX / 4))
        for n in range(len(self.statuses)):
            if n % sample == 0:
                statuses.append(self.statuses[n])
        statuses.append(self.statuses[-1])
        return statuses


    def flameMousemove(self, event):
        self.mousemoveCanvas(self.flameCanvas, self.calls, event)

    def timelineMousemove(self, event):
        self.mousemoveCanvas(self.timelineCanvas, self.statuses, event)
        self.mousemoveCanvas(self.timelineCanvas, self.markers, event)
    
    def mousemoveCanvas(self, canvas, views, event):
        if canvas.isDragging() or not hasattr(event.originalEvent, "offsetX"):
            return
        x, y, _, _ = canvas.absolute(event.originalEvent.offsetX, event.originalEvent.offsetY)
        for view in views:
            if view.inside(x, y):
                if not self.hover is view:
                    if self.hover:
                        self.hover.mouseleave(x, y)
                    view.mouseenter(x, y)
                    self.hover = view
                view.mousemove(x, y)

    def clickFlame(self, event):
        self.clickCanvas(self.flameCanvas, self.calls, event)

    def clickTimeline(self, event):
        self.clickCanvas(self.timelineCanvas, self.markers, event)

    def clickCanvas(self, canvas, views, event):
        if canvas.isDragging() or not hasattr(event.originalEvent, "offsetX"):
            return
        x, y, _, _ = canvas.absolute(event.originalEvent.offsetX, event.originalEvent.offsetY)
        for view in views:
            if view.inside(x, y):
                view.click(x, y)
                return True
        dialog.hide()


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
    StatusView.reset()
    MarkerView.reset()
    flamegraph.reset()
    loadLog(log)
    setUrl(log)
    js.jQuery("#explanation").text("")
    js.jQuery("#tabs-log").find("table").empty()


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


flamegraph = Flamegraph("#flameCanvas", "#timelineCanvas")


def showFlamegraph(data):
    log.log.load(data)
    js.jQuery("#debug").html("")
    debug("Load", profiler.getTime("Flamegraph.load"))
    flamegraph.load(log)
    flamegraph.redraw()


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


def resize(event=None):
    flamegraph.reset()
    height = js.jQuery(js.window).height() - 55
    filterHeight = js.jQuery("#filter").height() + 36
    tabHeight = height - js.jQuery(".tabs-header").height()
    padding = 24
    js.jQuery("body").css("height", height)
    js.jQuery(".main").css("height", height)
    js.jQuery(".tabs").css("height", height)
    width = js.jQuery(".tabs").width()
    flamegraph.resize(width, tabHeight - padding)
    js.jQuery("#tabs-tracing").css("height", tabHeight)
    js.jQuery("#tabs-design").css("height", tabHeight)
    js.jQuery("#tabs-log").css("height", tabHeight)
    js.jQuery("#tabs-explain").css("height", tabHeight)
    js.jQuery(".logs").css("height", height - filterHeight)
    js.jQuery(".tree").css("height", height - filterHeight - padding)

def main():
    setupLogHandlers()
    showAllLogs()
    loadLog(getLogFromUrl())
    debug("Logs", profiler.getTime("Logs.show"))
    js.jQuery(js.window).on("resize", pyodide.ffi.create_proxy(resize))
    resize()

main()