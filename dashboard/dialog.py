#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import js # type: ignore
import pyodide # type: ignore

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
        self.addCloseButton()
        self.canvas.canvas.parent().append(
            self.dialog
                .draggable()
                .resizable()
                .html(html)
                .css("left", x)
                .css("top", y)
                .addClass("ui-widget-content")
                .css("position", "absolute")
                .css("display", "block")
                .css("max-height", js.jQuery("body").height() - 100)
        )

    def hide(self):
        self.showing = False
        self.dialog.css("display", "none")

    def addCloseButton(self):
        self.dialog.append((js.jQuery("<div>")
            .addClass("dialog-close-button")
            .text("X")
            .click(pyodide.ffi.create_proxy(lambda event: self.hide()))
        ))
    
dialog = Dialog()