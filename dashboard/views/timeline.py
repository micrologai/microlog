#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from dashboard import canvas
from dashboard.views import config

class Timeline():
    def draw(self, canvas: canvas.Canvas):
        self.clear(canvas)
        tick =  0.1 if canvas.scale > 4 else \
                1000.0 if canvas.scale < 0.00390625 else \
                100.0 if canvas.scale < 0.0625 else \
                10.0 if canvas.scale < 0.5 else \
                1.0
        y = config.TIMELINE_OFFSET_Y + config.TIMELINE_HEIGHT 
        h = canvas.height()
        for n in range(0, 1000):
            second = n * tick
            x = second * config.PIXELS_PER_SECOND
            if x < 0:
                continue
            canvas.line(x, y - 13, x, h, 2, "#BBBA")
            label = f"{second:0.1f}s" if tick < 1 else f"{second:0.0f}s"
            cx = x - canvas.fromScreenDimension((len(label) * config.FONT_SIZE_SMALL / 4))
            canvas.text(cx, config.TIMELINE_OFFSET_Y + 7, label, "gray", canvas.fromScreenDimension(100), config.FONT_SMALL)
            if canvas.toScreenX(x) >= canvas.width():
                break

    def clear(self, canvas: canvas.Canvas):
        x, w = canvas.absolute(0, canvas.width())
        y = config.TIMELINE_OFFSET_Y + config.TIMELINE_HEIGHT 
        canvas.fillRect(x, config.TIMELINE_OFFSET_Y, w, config.TIMELINE_HEIGHT, "white")
        canvas.line(x, y, x + w, y, 3, "gray")