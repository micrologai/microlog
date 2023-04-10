#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

import js
from typing import List

from microlog.dashboard import canvas
 
WIDTH = 350
FLIP_DISTANCE = 70
MOUSE_OFFSET = 3
 
class Dialog():
    @classmethod
    def show(self, canvas: canvas.Canvas, x:float, y:float, html:str):
        x = canvas.toScreenX(x) + MOUSE_OFFSET
        if x + WIDTH > canvas.width():
            x -= WIDTH + FLIP_DISTANCE
        js.jQuery("#dialog") \
            .css("display", "block") \
            .css("left", x + MOUSE_OFFSET) \
            .css("top", y + MOUSE_OFFSET) \
            .html(html)

        height = js.jQuery("#dialog").height()
        if y + height > canvas.height():
            y -= height + MOUSE_OFFSET + FLIP_DISTANCE
            js.jQuery("#dialog") \
                .css("top", y + MOUSE_OFFSET)

        js.jQuery("#hairline") \
            .css("display", "block") \
            .css("left", x - MOUSE_OFFSET - 2) \
            .css("height", canvas.height())

    def hide(self):
        js.jQuery("#dialog").css("display", "none")
        js.jQuery("#hairline").css("display", "none")

dialog = Dialog()