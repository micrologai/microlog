#
# Microlog. Copyright (c) 2023 laffra, dcharbon. All rights reserved.
#

from dashboard import canvas
from dashboard import config
from dashboard import profiler

class Timeline():
    @profiler.profile("Timeline.draw")
    def draw(self, canvas: canvas.Canvas):
        self.clear(canvas)
        self.drawTicks(canvas)
    
    def drawTicks(self, canvas):
        y = config.TIMELINE_OFFSET_Y + config.TIMELINE_HEIGHT 
        h = canvas.height()
        lines = []
        ticks = []
        texts = []
        tick = self.getTick(canvas)

        def addTick(n, x):
            second = n * tick
            ticks.append((x, y - 13, x, h))
            label = f"{second:0.2f}s" if tick < 0.1 else f"{second:0.1f}s" if tick < 1 else f"{second:0.0f}s"
            cx = x - canvas.fromScreenDimension((len(label) * config.FONT_SIZE_SMALL / 4))
            texts.append((cx, config.TIMELINE_OFFSET_Y + 23, label, "gray", canvas.fromScreenDimension(100)))
            lines.append((x, 0, x, config.TIMELINE_OFFSET_Y))

        self.drawVisibleSeconds(canvas, addTick)
        canvas.lines(ticks, 1, "gray")
        canvas.lines(lines, 1, "gray")
        canvas.texts(texts, config.FONT_SMALL)

    def getTick(self, canvas):
        return 0.01 if canvas.scaleX > 128 else \
               0.1 if canvas.scaleX > 4 else \
               1000.0 if canvas.scaleX < 0.00390625 else \
               100.0 if canvas.scaleX < 0.0625 else \
               10.0 if canvas.scaleX < 0.5 else \
               1.0

    def drawVisibleSeconds(self, canvas, draw):
        tick = self.getTick(canvas)
        for n in range(0, 1000):
            second = n * tick
            x = second * config.PIXELS_PER_SECOND
            if x < 0:
                continue
            draw(n, x)
            if canvas.toScreenX(x) >= canvas.width():
                break

    def clear(self, canvas: canvas.Canvas):
        x, _, w, _ = canvas.absolute(0, 0, canvas.width())
        y = config.TIMELINE_OFFSET_Y + config.TIMELINE_HEIGHT 
        canvas.fillRect(x, config.TIMELINE_OFFSET_Y, w, config.TIMELINE_HEIGHT, "white")
        canvas.line(x, y, x + w, y, 3, "gray")