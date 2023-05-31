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
        from dashboard.views import config
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
        js.jQuery("#hairline") \
            .css("display", "block") \
            .css("top", js.jQuery(".tabs-header").height() + 3) \
            .css("left", screenX - MOUSE_OFFSET - 2) \
            .css("height", config.STATS_HEIGHT)
        print("dialog", x, y, screenX, screenY)

    def hide(self):
        js.jQuery("#dialog").css("display", "none")
        js.jQuery("#hairline").css("display", "none")

dialog = Dialog()