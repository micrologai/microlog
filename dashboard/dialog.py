#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import js # type: ignore
import pyodide # type: ignore
from typing import List

from dashboard import canvas
 
FLIP_DISTANCE = 70
MOUSE_OFFSET = 20
 
class Dialog():
    def __init__(self):
        self.showing = False
        self.dialog = js.jQuery("#dialog")

    def show(self, canvas: canvas.Canvas, x:float, y:float, html:str):
        self.canvas = canvas
        self.showing = True
        self.createDialog(html)
        self.positionDialog(x, y)
        self.addCloseButton()

    def hide(self):
        self.showing = False
        self.dialog.css("display", "none")

    def createDialog(self, html):
        (self.dialog
            .draggable()
            .resizable()
            .html(html)
            .addClass("ui-widget-content")
            .css("display", "block")
            .css("max-height", js.jQuery("body").height() - 100))
    
    def addCloseButton(self):
        self.dialog.append((js.jQuery("<div>")
            .addClass("dialog-close-button")
            .text("X")
            .click(pyodide.ffi.create_proxy(lambda event: self.hide()))
        ))
    
    def positionDialog(self, x, y):
        width = self.dialog.width()
        height = self.dialog.height()
        if not js.parseFloat(self.dialog.css("left")):
            screenX = self.canvas.toScreenX(x) + MOUSE_OFFSET
            screenY = y + MOUSE_OFFSET + js.jQuery(".tabs-header").height()
            x = screenX
            if screenX + width + FLIP_DISTANCE > self.canvas.width():
                x = max(0, screenX - width - FLIP_DISTANCE)
            y = screenY
            if screenY + height + FLIP_DISTANCE > self.canvas.height():
                y = max(0, screenY - height - FLIP_DISTANCE)
            self.dialog.css("left", x).css("top", y)

dialog = Dialog()