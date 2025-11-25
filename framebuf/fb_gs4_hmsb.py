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

from ueink.core.logging import logger

from itertools import repeat


def decorate_gs4_hmsb(fb: "FrameBuffer") -> None:
    fb._getpixel = _getpixel
    fb._setpixel = _setpixel
    fb._fill_rect = _fill_rect


def _setpixel(fb: "FrameBuffer", x: int, y: int, col: int) -> None:
    color = col & 0x0F
    offset = (x + y * fb.stride) // 2
    if x % 2:
        fb.buf[offset] = (color & 0x0F) | (fb.buf[offset] & 0xF0)
    else:
        fb.buf[offset] = (color << 4) | (fb.buf[offset] & 0x0F)


def _getpixel(fb: "FrameBuffer", x: int, y: int) -> int:
    if x % 2:
        return fb.buf[(x + y * fb.stride) // 2] & 0x0F
    else:
        return fb.buf[(x + y * fb.stride) // 2] >> 4


def _fill_rect(fb: "FrameBuffer", x: int, y: int, w: int, h: int, c: int) -> None:
    if w <= 0 or h <= 0:
        return

    color_right = c & 0x0F
    offset = (x + y * fb.stride) // 2
    color_left = color_right << 4
    col_pixel_pair = color_left | color_right
    bytes_till_next = (fb.stride - w) // 2
    odd_x = x % 2
    pairs_line = memoryview(bytes(repeat(col_pixel_pair, (w >> 1) + 1)))

    for _ in range(h):
        width = w

        if odd_x:
            fb.buf[offset] = (fb.buf[offset] & 0xF0) | color_right
            offset += 1
            width -= 1

        bytes_width = width // 2
        fb.buf[offset : offset + bytes_width] = pairs_line[:bytes_width]
        offset += bytes_width

        if width % 2:
            fb.buf[offset] = color_left | (fb.buf[offset] & 0x0F)
            if not odd_x:
                offset += 1
                width += 1

        offset += bytes_till_next


__all__ = ("decorate_gs4_hmsb",)
