#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from __future__ import annotations

from collections import defaultdict
import js
import json
import itertools
import math
import pyodide
import time
from typing import List

from microlog.stack import Call
from microlog import profiler

from dashboard.dialog import dialog

from dashboard.views import status
from dashboard.views import config
from dashboard.views import View
from dashboard.views import sanitize

from dashboard import canvas
from dashboard import colors


class CallView(View):
    model = Call
    popupTimer = js.setTimeout(pyodide.ffi.create_proxy(lambda: None), 1)

    def __init__(self, canvas: canvas.Canvas, event):
        View.__init__(self, canvas, event)
        self.h = config.LINE_HEIGHT
        self.y = self.depth * config.LINE_HEIGHT + config.FLAME_OFFSET_Y
        self.color = colors.getColor(self.callSite.name)

    def getLabel(self):
        w = self.canvas.toScreenDimension(self.w)
        if w > 300:
            return f"{self.getFullName()} (at {self.when:0.2f} duration: {self.duration:0.2f}s)"
        elif w > 200:
            return f"{self.getShortName()} (at {self.when:0.2f} duration: {self.duration:0.2f}s)"
        else:
            return self.getShortName()

    @classmethod
    @profiler.profile("CallView.drawAll")
    def drawAll(cls, canvas: canvas.Canvas, calls):
        x, w = canvas.absolute(0, canvas.width())
        y = config.TIMELINE_OFFSET_Y + config.TIMELINE_HEIGHT 
        canvas.fillRect(x, y, w, canvas.height(), "#222")
        canvas.fillRects(
            (call.x, call.y, call.w, call.h, call.color)
            for call in calls
        )
        dx = canvas.fromScreenDimension(4)
        canvas.texts(
            [
                (
                    call.x + dx,
                    call.y + call.h - 8,
                    call.getLabel(),
                    "#111111",
                    call.w
                )
                for call in calls
                if canvas.toScreenDimension(call.w) > 25
            ], config.FONT_REGULAR
        )
        canvas.lines(
            itertools.chain([
                ( call.x, call.y, call.x, call.y + call.h )
                for call in calls
            ]),
            1,
            "gray"
        )
        canvas.lines(
            itertools.chain([
                ( call.x, call.y + call.h, call.x + call.w, call.y + call.h )
                for call in calls
            ]),
            1,
            "gray"
        )

    def _draw(self, fill, color):
        w = self.canvas.toScreenDimension(self.w)
        if w > 0:
            self.canvas.fillRect(self.x, self.y, self.w, self.h - 1, fill)
            self.canvas.line(self.x, self.y, self.x + self.w, self.y, 1, "#DDD")
            self.canvas.line(self.x, self.y, self.x, self.y + self.h, 1, "#AAA")
        if w > 25:
            dx = self.canvas.fromScreenDimension(4)
            self.canvas.text(self.x + dx, self.y + 2, self.getLabel(), color, self.w)
 
    def offscreen(self):
        x = self.canvas.toScreenX(self.x)
        w = self.canvas.toScreenDimension(self.w)
        return w < 2 or x + w < 0 or x > self.canvas.width()
    
    def getFullName(self):
        return self.callSite.name
    
    def getShortName(self):
        parts = self.callSite.name.split(".")
        name = parts[-1]
        if name == "<module>":
            name = parts[-2] or parts[-3]
        return name

    def mouseenter(self, x, y):
        View.mouseenter(self, x, y)

    def mousemove(self, x, y):
        js.clearTimeout(self.popupTimer)
        CallView.popupTimer = js.setTimeout(pyodide.ffi.create_proxy(lambda: self.showPopup(x, y)), config.CALL_HOVER_DIALOG_DELAY)

    def showPopup(self, x, y):
        if self.canvas.isDragging():
            return
        self.canvas.redraw()
        similar = [call for call in self.others() if self.isSimilar(call)]
        average = sum(call.duration for call in similar) / len(similar)
        anomalies = [call for call in similar if call.duration - average > 0.1 and call.duration / average > 1.3]
        cpu = self.getCpu()
        detailsId = f"call-details-{id(self)}"
        name = sanitize(self.callSite.name).replace("..",".")
        link = f"<a href=vscode://file/{self.callSite.filename}:{self.callSite.lineno}:1>{name}</a>"
        dialog.show(self.canvas, x, y, f"""
            <b>{link}</b><br>
            This call happened at: {self.when:.3f}s<br>
            It lasted for: {self.duration:.3f}s<br>
            Average duration: {average:.3f}s<br>
            CPU usage during this call: {cpu:.1f}s {"😡" if cpu < 80 else ""}<br>
            Called by: {sanitize(self.callerSite.name).replace("..", ".")}<br>
            <div id="{detailsId}"><br><span style="color:gray">loading details...</span></div>
        """)
        if len(similar) > 1000:
            js.setTimeout(pyodide.ffi.create_proxy(lambda: self.addSimilarCalls(f"#{detailsId}", cpu, similar, anomalies)), 1)
        else:
            self.addSimilarCalls(f"#{detailsId}", cpu, similar, anomalies)
        self._draw("red", "white")

    def mouseleave(self, x, y):
        View.mouseleave(self, x, y)
        self.draw()
        
    def getCpu(self):
        stats: List[status.StatusView] = [
            view for view in View.instances[status.StatusView]
            if isinstance(view, status.StatusView) and view.when >= self.when and view.when <= self.when + self.duration
        ]
        return sum(stat.process.cpu for stat in stats) / len(stats) if stats else 0

    def isAnomaly(self, call, anomalies):
        for anomaly in anomalies:
            if call is anomaly:
                return True

    def getAllCalls(self, similar, anomalies):
        maxDuration = max(call.duration for call in similar)
        def color(call: CallView):
            return "red" if self.isAnomaly(call, anomalies) else "green"
        return "".join([
            f"""<tr>
                <td style="text-align: right">{call.when:.3f}s</td>
                <td style="text-align: right">{call.duration:.3f}s</td>
                <td><div style="background: {color(call)}; height: 12px; width:{call.duration * 150 / maxDuration}px"></div></td>
            </tr>"""
            for call in sorted(similar, key=lambda call: -call.duration)
        ])

    def getSimilarCallHTML(self, similar, anomalies):
        allCalls = self.getAllCalls(similar, anomalies)
        return f"""<br>There are {len(similar)} calls in this run:
            <div style="height: 300px; overflow-y: scroll">
                <table>
                    <hr>
                        <td style="text-align: right"><b>When</b></td>
                        <td style="text-align: right"><b>&nbsp;&nbsp;Time</b></td>
                </hr>
                {allCalls}
                </table>
            </div>
        """
            
    def getAnomaliesHTML(self, cpu, anomalies):
        return f"""
            <br>
            <img src="data:image/webp;base64,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">
            <br>
            Microlog detected {len(anomalies)} likely anomalies.<br>
            The current call {"appears to be an anomaly" if self.isAnomaly(self, anomalies) else "looks average"}.<br>
        """

    def addSimilarCalls(self, detailsId: str, cpu: float, similar: List[Call], anomalies: List[Call]):
        parts = []
        if math.ceil(cpu) > 0 and cpu < 80:
            parts.append("<span style='color:red'><b>CPU usage is low during this call.</b></span><br>")
        if len(anomalies) > 1:
            parts.append(self.getAnomaliesHTML(cpu, anomalies))
        if len(similar) > 1:
            parts.append(self.getSimilarCallHTML(similar, anomalies))
        js.jQuery(detailsId).html("".join(parts))

    def __eq__(self, other):
        return isinstance(other, CallView) and self.callSite == other.callSite and self.callerSite == other.callerSite