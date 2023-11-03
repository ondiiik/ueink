# MicroPython EInk displays drivers - python variant of frame buffer
#
# Based on modframebuf.c
#
# MIT License
# Copyright (c) 2023 Ondrej Sienczak
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
from __future__ import annotations

from .fb_gs4_hmsb import decorate_gs4_hmsb
from .fb_mhlsb import decorate_mhlsb
from .fb_mhmsb import decorate_mhmsb
from .fb_mvlsb import decorate_mvlsb
from .font import font_petme128_8x8

MVLSB = 0
MONO_VLSB = 0
RGB565 = 1
GS2_HMSB = 5
GS4_HMSB = 2
GS8 = 6
MONO_HLSB = 3
MONO_HMSB = 4

_fb_format_decorator = {
    GS4_HMSB: (decorate_gs4_hmsb, 1),
    MONO_HLSB: (decorate_mhlsb, 7),
    MONO_HMSB: (decorate_mhmsb, 7),
    MVLSB: (decorate_mvlsb, 0),
}


class FrameBuffer:
    def __init__(
        self,
        buf: bytearray,
        width: int,
        height: int,
        fmt: int,
        stride: int | None = None,
    ) -> None:
        decorate, align_factor = _fb_format_decorator[fmt]

        self.buf = buf
        self.width = width
        self.height = height
        self.format = fmt
        self.stride = (
            (width if stride is None else stride) + align_factor
        ) & ~align_factor

        decorate(self)

    def pixel(self, x: int, y: int, col: int = -1) -> int | None:
        if 0 <= x and x < self.width and 0 <= y and y < self.height:
            if col < 0:
                return self._getpixel(self, x, y)
            else:
                self._setpixel(self, x, y, col)
                return None

    def fill(self, col: int) -> None:
        self._fill_rect(self, 0, 0, self.width, self.height, col)

    def rect(
        self, x: int, y: int, width: int, height: int, col: int, fill: bool = False
    ) -> None:
        if fill:
            self._fill_rect(self, x, y, width, height, col)
        else:
            self._fill_rect(self, x, y, width, 1, col)
            self._fill_rect(self, x, y + height - 1, width, 1, col)
            self._fill_rect(self, x, y, 1, height, col)
            self._fill_rect(self, x + width - 1, y, 1, height, col)

    def hline(self, x: int, y: int, w: int, col: int) -> None:
        self._fill_rect(self, x, y, w, 1, col)

    def vline(self, x: int, y: int, h: int, col: int) -> None:
        self._fill_rect(self, self, x, y, 1, h, col)

    def line(self, x1: int, y1: int, x2: int, y2: int, col: int) -> None:
        dx = x2 - x1
        if dx > 0:
            sx = 1
        else:
            dx = -dx
            sx = -1

        dy = y2 - y1
        if dy > 0:
            sy = 1
        else:
            dy = -dy
            sy = -1

        steep = dy > dx
        if steep:
            x1, y1 = y1, x1
            dx, dy = dy, dx
            sx, sy = sy, sx

        e = 2 * dy - dx
        for _ in range(dx):
            if steep:
                if 0 <= y1 and y1 < self.width and 0 <= x1 and x1 < self.height:
                    self._setpixel(self, y1, x1, col)
            else:
                if 0 <= x1 and x1 < self.width and 0 <= y1 and y1 < self.height:
                    self._setpixel(self, x1, y1, col)

            while e >= 0:
                y1 += sy
                e -= 2 * dx

            x1 += sx
            e += 2 * dy

        if 0 <= x2 and x2 < self.width and 0 <= y2 and y2 < self.height:
            self._setpixel(self, x2, y2, col)

    def ellipse(
        self,
        cx: int,
        cy: int,
        xradius: int,
        yradius: int,
        col: int,
        fill: bool = False,
        msk: int = 0x0F,
    ) -> None:
        mask = 0x0F if fill else 0
        mask |= msk & 0x0F
        two_asquare = 2 * xradius * xradius
        two_bsquare = 2 * yradius * yradius
        x = xradius
        y = 0
        xchange = yradius * yradius * (1 - 2 * xradius)
        ychange = xradius * xradius
        ellipse_error = 0
        stoppingx = two_bsquare * xradius
        stoppingy = 0
        while stoppingx >= stoppingy:
            self._draw_ellipse_points(cx, cy, x, y, col, mask)
            y += 1
            stoppingy += two_asquare
            ellipse_error += ychange
            ychange += two_asquare
            if (2 * ellipse_error + xchange) > 0:
                x -= 1
                stoppingx -= two_bsquare
                ellipse_error += xchange
                xchange += two_bsquare
        x = 0
        y = yradius
        xchange = yradius * yradius
        ychange = xradius * xradius * (1 - 2 * yradius)
        ellipse_error = 0
        stoppingx = 0
        stoppingy = two_asquare * yradius
        while stoppingx <= stoppingy:
            self._draw_ellipse_points(cx, cy, x, y, col, mask)
            x += 1
            stoppingx += two_bsquare
            ellipse_error += xchange
            xchange += two_bsquare
            if (2 * ellipse_error + ychange) > 0:
                y -= 1
                stoppingy -= two_asquare
                ellipse_error += ychange
                ychange += two_asquare

    def text(self, txt: str, x: int, y: int, col: int = 1) -> None:
        for cc in txt:
            c = ord(cc)
            if c < 32 or c > 127:
                c = 127
            o = (c - 32) * 8
            chr_data = font_petme128_8x8[o : o + 8]
            for vline_data in chr_data:
                if 0 <= x and x < self.width:
                    yy = y
                    while vline_data:
                        if vline_data & 1 and 0 <= y and y < self.height:
                            self._setpixel(self, x, yy, col)
                        vline_data >>= 1
                        yy += 1
                x += 1

    def blit(
        self,
        source: FrameBuffer,
        x: int,
        y: int,
        key: int = -1,
        palette: FrameBuffer | None = None,
    ) -> None:
        if (
            x >= self.width
            or y >= self.height
            or -x >= source.width
            or -y >= source.height
        ):
            return
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = max(0, -x)
        y1 = max(0, -y)
        x0end = min(self.width, x + source.width)
        y0end = min(self.height, y + source.height)
        while y0 < y0end:
            cx1 = x1
            for cx0 in range(x0, x0end):
                col = source._getpixel(source, cx1, y1)
                if palette:
                    col = palette._getpixel(palette, col, 0)
                if col != key:
                    self._setpixel(self, cx0, y0, col)
                cx1 += 1
            y1 += 1
            y0 += 1

    def scroll(self, xstep: int, ystep: int) -> None:
        if xstep < 0:
            sx = 0
            xend = self.width + xstep
            if xend <= 0:
                return
            dx = 1
        else:
            sx = self.width - 1
            xend = xstep - 1
            if xend >= sx:
                return
            dx = -1
        if ystep < 0:
            y = 0
            yend = self.height + ystep
            if yend <= 0:
                return
            dy = 1
        else:
            y = self.height - 1
            yend = ystep - 1
            if yend >= y:
                return
            dy = -1
        while y != yend:
            for x in range(sx, xend, dx):
                self._setpixel(self, x, y, self._getpixel(self, x - xstep, y - ystep))
            y += dy

    def poly(self, x: int, y: int, coords: list, col: int, fill: bool = False) -> None:
        n_poly = len(coords) // 2
        bufinfo = coords[: n_poly * 2]

        if not bufinfo:
            return

        if fill:
            # This implements an integer version of http://alienryderflex.com/polygon_fill/

            # The idea is for each scan line, compute the sorted list of x
            # coordinates where the scan line intersects the polygon edges,
            # then fill between each resulting pair.

            # Restrict just to the scan lines that include the vertical extent of
            # this polygon.
            y_min = min(bufinfo[1::2])
            y_max = max(bufinfo[1::2])

            for row in range(y_min, y_max):
                # Each node is the x coordinate where an edge crosses this scan line.
                nodes = list()
                px1 = bufinfo[0]
                py1 = bufinfo[1]
                i = n_poly * 2 - 1
                while True:
                    py2 = bufinfo[i]
                    i -= 1
                    px2 = bufinfo[i]
                    i -= 1

                    # Don't include the bottom pixel of a given edge to avoid
                    # duplicating the node with the start of the next edge. This
                    # will miss some pixels on the boundary, and in particular
                    # at a local minima or inflection point.
                    if py1 != py2 and (
                        (py1 > row and py2 <= row) or (py1 <= row and py2 > row)
                    ):
                        node = (
                            32 * px1 + 32 * (px2 - px1) * (row - py1) / (py2 - py1) + 16
                        ) / 32
                        nodes.append(node)
                    elif row == max(py1, py2):
                        # At local-minima, try and manually fill in the pixels that get missed above.
                        if py1 < py2:
                            self._setpixel_checked(x + px2, y + py2, col, 1)
                        elif py2 < py1:
                            self._setpixel_checked(x + px1, y + py1, col, 1)
                        else:
                            # Even though this is a hline and would be faster to
                            # use fill_rect, use line() because it handles x2 <
                            # x1.
                            self.line(x + px1, y + py1, x + px2, y + py2, col)

                    px1 = px2
                    py1 = py2

                    if i < 0:
                        break

                if not nodes:
                    continue

                # Sort the nodes left-to-right (bubble-sort for code size).
                nodes.sort()

                # Fill between each pair of nodes.
                for i in range(0, len(nodes), 2):
                    self._fill_rect(
                        self,
                        x + nodes[i],
                        y + row,
                        (nodes[i + 1] - nodes[i]) + 1,
                        1,
                        col,
                    )
        else:
            # Outline only.
            px1 = bufinfo[0]
            py1 = bufinfo[1]
            i = n_poly * 2 - 1
            while True:
                py2 = bufinfo[i]
                i -= 1
                px2 = bufinfo[i]
                i -= 1
                self.line(x + px1, y + py1, x + px2, y + py2, col)
                px1 = px2
                py1 = py2
                if i < 0:
                    break

    def _draw_ellipse_points(
        self, cx: int, cy: int, x: int, y: int, col: int, mask: int
    ) -> None:
        if mask & 0x0F:
            if mask & 0x01:
                self._fill_rect(self, cx, cy - y, x + 1, 1, col)
            if mask & 0x02:
                self._fill_rect(self, cx - x, cy - y, x + 1, 1, col)
            if mask & 0x04:
                self._fill_rect(self, cx - x, cy + y, x + 1, 1, col)
            if mask & 0x08:
                self._fill_rect(self, cx, cy + y, x + 1, 1, col)
        else:
            self._setpixel_checked(cx + x, cy - y, col, mask & 0x01)
            self._setpixel_checked(cx - x, cy - y, col, mask & 0x02)
            self._setpixel_checked(cx - x, cy + y, col, mask & 0x04)
            self._setpixel_checked(cx + x, cy + y, col, mask & 0x08)

    def _setpixel_checked(self, x: int, y: int, col: int, mask: int) -> None:
        if mask and 0 <= x and x < self.width and 0 <= y and y < self.height:
            self._setpixel(self, x, y, col)


__all__ = (
    "FrameBuffer",
    "GS2_HMSB",
    "GS4_HMSB",
    "GS8",
    "MONO_HLSB",
    "MONO_HMSB",
    "MONO_VLSB",
    "MVLSB",
    "RGB565",
)
