#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import js # type: ignore
from typing import List

from dashboard import canvas
 
FLIP_DISTANCE = 70
MOUSE_OFFSET = 20
 
class Dialog():
    def show(self, canvas: canvas.Canvas, x:float, y:float, html:str):
        self.showDialog(canvas, x, y, html)

    def showDialog(self, canvas: canvas.Canvas, x:float, y:float, html:str):
        dialog = js.jQuery("#dialog").css("display", "block").html(html)
        width = dialog.width()
        height = dialog.height()
        screenX = canvas.toScreenX(x) + MOUSE_OFFSET
        screenY = y + MOUSE_OFFSET + js.jQuery(".tabs-header").height()
        x = screenX
        if screenX + width + FLIP_DISTANCE > canvas.width():
            x = max(0, screenX - width - FLIP_DISTANCE)
        y = screenY
        if screenY + height + FLIP_DISTANCE > canvas.height():
            y = max(0, screenY - height - FLIP_DISTANCE)
        dialog.css("left", x).css("top", y)

    def hide(self):
        js.jQuery("#dialog").css("display", "none")
        js.jQuery("#hairline").css("display", "none")

dialog = Dialog()