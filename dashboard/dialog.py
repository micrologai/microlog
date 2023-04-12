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
        width = dialog.width()
        height = dialog.height()
        screenX = canvas.toScreenX(x) + MOUSE_OFFSET
        screenY = y + MOUSE_OFFSET
        dialog \
            .css("left", screenX if screenX + width < canvas.width() else screenX - width - FLIP_DISTANCE) \
            .css("top", screenY if screenY + height < canvas.height() else screenY - height - FLIP_DISTANCE)

        js.jQuery("#hairline") \
            .css("display", "block") \
            .css("left", screenX - MOUSE_OFFSET - 2) \
            .css("height", canvas.height())

    def hide(self):
        js.jQuery("#dialog").css("display", "none")
        js.jQuery("#hairline").css("display", "none")

dialog = Dialog()