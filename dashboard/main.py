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
        self.flameCanvas = self.createCanvas(self.flameElementId, self.drawFlame, self.clickFlame, self.dragFlame, self.zoomFlame, self.flameMousemove, fixedScaleY=True)
        self.timelineCanvas = self.createCanvas(self.timelineElementId, self.drawTimeline, self.clickTimeline, self.dragTimeline, self.zoomTimeline, self.timelineMousemove, fixedY=True, fixedScaleY=True)
        js.jQuery(".tabs").on("tabsactivate", pyodide.ffi.create_proxy(lambda event, ui: self.activateTab(event, ui)))
        js.jQuery("#filter").val(getFilterFromUrl())

    def dragFlame(self, dx, dy):
        self.timelineCanvas.drag(dx, dy)
        CallView.positionThreads(self.flameCanvas)
        self.drawTimeline()

    def zoomFlame(self, x, y, scale):
        self.timelineCanvas.zoom(x, y, scale)
        self.drawTimeline()

    def dragTimeline(self, dx, dy):
        self.flameCanvas.drag(dx, dy)
        self.drawFlame()

    def zoomTimeline(self, x, y, scale):
        self.flameCanvas.zoom(x, y, scale)
        self.drawFlame()

    def resize(self, width, height):
        timelineHeight = config.TIMELINE_OFFSET_Y + config.TIMELINE_HEIGHT 
        self.timelineCanvas.width(width)
        self.timelineCanvas.height(timelineHeight)
        self.flameCanvas.width(width)
        self.flameCanvas.height(height - timelineHeight)
        self.redraw()

    def createCanvas(self, elementId, redraw, click, drag, zoom, mousemove, fixedY=False, fixedScaleY=False):
        return (canvas.Canvas(elementId, redraw, drag, zoom, click, minOffsetX=48, minOffsetY=0, fixedY=fixedY, fixedScaleY=fixedScaleY)
            .on("mousemove", mousemove))

    def activateTab(self, event, ui):
        self.currentTab = ui.newTab.text()
        self.redraw()

    def reset(self):
        self.timelineCanvas.reset()
        self.flameCanvas.reset()
        self.hover = None
        CallView.reset()
        StatusView.reset()
        MarkerView.reset()

    @profiler.profile("Flamegraph.convertLog")
    def convertLog(self, log):
        self.calls = [ CallView(self.flameCanvas, model) for model in log.log.calls ]
        self.statuses = [ StatusView(self.timelineCanvas, model) for model in log.log.statuses ]
        self.markers = [ MarkerView(self.timelineCanvas, model) for model in log.log.markers ]

    @profiler.profile("Flamegraph.showStatus")
    def showStatus(self, logEntries, index):
        if self.statuses and index < len(self.statuses):
            logEntries.append((self.statuses[index].when, str(self.statuses[index]), ""))

    @profiler.report("Flamegraph.load")
    def load(self, log):
        self.convertLog(log)
        statusIndex = 0
        logEntries = []
        self.showStatus(logEntries, 0)
        for marker in self.markers:
            while self.statuses[statusIndex].when < marker.when and statusIndex < len(self.statuses) - 1:
                statusIndex += 1
            logEntries.append((marker.when, markdown.toHTML(marker.message), marker.formatStack(full=False)))
            self.showStatus(logEntries, statusIndex)
        self.addLogEntries(logEntries)
        self.showStatus(logEntries, -1)
        self.hover = None
        js.jQuery(self.flameElementId).empty()
        js.jQuery(self.timelineElementId).empty()
   
    @profiler.report("Redrawing the whole UI.")
    def redraw(self, event=None):
        if self.currentTab == "Timeline":
            self.drawTimeline()
            self.drawFlame()
        elif self.currentTab == "Design":
            self.design = Design(self.calls)
            self.design.draw()
        elif self.currentTab == "Explanation":
            explain(getLogFromUrl())
        elif self.currentTab == "Tips":
            self.tips = Tips(self.calls)
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

    def loading(self, name):
        self.clear()
        self.timelineCanvas.text(-20, 20, f"Loading {name}...", color="#BBB", font="16px Arial")

    def clear(self, canvas=None):
        if canvas:
            canvas.clear("#222")
        else:
            self.flameCanvas.clear("#222")
            self.timelineCanvas.clear("#222")
        dialog.hide()
        js.jQuery(".highlight").css("left", 10000)

    @profiler.report("Flamegraph.drawTimeline")
    def drawTimeline(self, event=None):
        self.clear(self.timelineCanvas)
        js.jQuery("#hairline").css("display", "none")
        self.hover = None
        self.drawStatuses()
        self.drawMarkers()
        self.timeline.draw(self.timelineCanvas)

    @profiler.profile("Flamegraph.drawStatuses")
    def drawStatuses(self):
        canvasScaleX = self.flameCanvas.scaleX
        canvasOffsetX = self.flameCanvas.offsetX
        canvasWidth = self.flameCanvas.width()
        StatusView.drawAll(self.timelineCanvas, [
            view for view in self.sampleStatuses()
            if not view.offscreen(canvasScaleX, canvasOffsetX, canvasWidth)
        ])

    @profiler.profile("Flamegraph.drawMarkers")
    def drawMarkers(self):
        canvasScaleX = self.flameCanvas.scaleX
        canvasOffsetX = self.flameCanvas.offsetX
        canvasWidth = self.flameCanvas.width()
        MarkerView.drawAll(self.timelineCanvas, [
            view for view in self.markers
            if not view.offscreen(canvasScaleX, canvasOffsetX, canvasWidth)
        ])
        
    @profiler.report("Flamegraph.drawFlame")
    def drawFlame(self, event=None):
        self.clear(self.flameCanvas)
        js.jQuery("#hairline").css("display", "none")
        canvasScaleX = self.flameCanvas.scaleX
        canvasOffsetX = self.flameCanvas.offsetX
        canvasWidth = self.flameCanvas.width()
        CallView.drawAll(self.flameCanvas, [
            view for view in self.calls
            if not view.offscreen(canvasScaleX, canvasOffsetX, canvasWidth)
        ])
        
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
        canvasScaleX = self.flameCanvas.scaleX
        canvasOffsetX = self.flameCanvas.offsetX
        canvasWidth = self.flameCanvas.width()
        for view in views:
            if not view.offscreen(canvasScaleX, canvasOffsetX, canvasWidth) and view.inside(x, y):
                if not self.hover is view:
                    if self.hover:
                        self.hover.mouseleave(x, y)
                    view.mouseenter(x, y)
                    self.hover = view
                view.mousemove(x, y)

    def clickFlame(self, x, y):
        self.clickCanvas(self.flameCanvas, self.calls, x, y)

    def clickTimeline(self, x, y):
        self.clickCanvas(self.timelineCanvas, self.markers, x, y)

    def clickCanvas(self, canvas, views, x, y):
        x, y, _, _ = canvas.absolute(x, y)
        for view in views:
            if view.inside(x, y):
                print("click", x, y, view)
                view.click(x, y)
                return True
        dialog.hide()


def setUrl(log=None):
    if not "Electron" in js.navigator.userAgent:
        filter = js.jQuery(".filter").val()
        if log:
            url = f"#{log}/{filter}"
            js.history.pushState(js.object(), "", url)


def showLog(log):
    flamegraph.clear()
    flamegraph.reset()
    loadLog(log)
    setUrl(log)
    js.jQuery("#explanation").text("")
    js.jQuery("#tabs-log").find("table").empty()


def loadLog(name):
    flamegraph.loading(name)
    url = f"zip/{name}"
    js.jQuery.get(url, pyodide.ffi.create_proxy(lambda data, status, xhr: showFlamegraph(data)))


def explain(name):
    if not js.jQuery("#explanation").text():
        message = "Asking OpenAI to explain this program..."
        if js.document.location.host == 'micrologai.github.io':
            "This feature is not enabled on Github Pages."
        js.jQuery("#explanation").text(message)
        url = f"explain/{name}"
        js.jQuery.get(url, pyodide.ffi.create_proxy(lambda data, status, xhr: js.jQuery("#explanation").html(markdown.toHTML(data))))


@profiler.profile("Logs.show")
def showAllLogs():
    dialog.hide()
    filter = js.jQuery(".filter").val()
    url = f"logs?filter={filter}"
    js.jQuery.get(url, pyodide.ffi.create_proxy(lambda data, status, xhr: renderLogs(data.strip().split("\n"))))
    js.jQuery(".logs") \
        .empty() \
        .append(js.jQuery("<img>").addClass("loading").attr("src", "/microlog/images/spinner.gif"))


def deleteLog(name, doneHandler):
    url = f"delete/{name}"
    js.jQuery.get(url, pyodide.ffi.create_proxy(lambda data, status, xhr: doneHandler()))


def getLogFromUrl():
    hash = js.document.location.hash
    if hash:
        app, name, _ = hash[1:].split("/")
        return f"{app}/{name}"
    return ""

def getFilterFromUrl():
    hash = js.document.location.hash
    if hash:
        _, _, filter = hash[1:].split("/")
        return filter
    return ""


def renderLogs(logList: List[str]):
    from collections import defaultdict
    if not any(logList):
        js.jQuery(".logs").empty().append(js.jQuery("<span>").css("color", "pink").text("No matching logs found")),
        return
    def tree():
        return defaultdict(tree)
    logs = tree()
    for log in [log for log in reversed(logList) if log]:
        application, name = log.split("/")
        if application != "-":
            logs[application][name.replace(".log", "")]
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
    flamegraph.load(log)
    flamegraph.redraw()


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
    js.jQuery(js.window).on("resize", pyodide.ffi.create_proxy(resize))
    resize()

main()