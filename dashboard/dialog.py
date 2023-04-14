#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import js
from typing import List

from dashboard import canvas
 
FLIP_DISTANCE = 70
MOUSE_OFFSET = 3
 
class Dialog():
    @classmethod
    def show(self, canvas: canvas.Canvas, x:float, y:float, html:str):
        dialog = js.jQuery("#dialog").css("display", "block").html(html)
        X = canvas.canvas.offset().left
        width = dialog.width()
        height = dialog.height()
        screenX = canvas.toScreenX(x) + MOUSE_OFFSET
        screenY = y + MOUSE_OFFSET
        dialog \
            .css("left", X + screenX if screenX + width + FLIP_DISTANCE < canvas.width() else max(0, screenX - width - FLIP_DISTANCE)) \
            .css("top", screenY if screenY + height + FLIP_DISTANCE < canvas.height() else max(0, screenY - height - FLIP_DISTANCE))

        js.jQuery("#hairline") \
            .css("display", "block") \
            .css("left", X + screenX - MOUSE_OFFSET - 2) \
            .css("height", canvas.height())

    def hide(self):
        js.jQuery("#dialog").css("display", "none")
        js.jQuery("#hairline").css("display", "none")

dialog = Dialog()