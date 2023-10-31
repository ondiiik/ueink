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


def decorate_gs4_hmsb(fb: "FrameBuffer") -> None:
    fb._getpixel = _getpixel
    fb._setpixel = _setpixel
    fb._fill_rect = _fill_rect


def _setpixel(fb: "FrameBuffer", x: int, y: int, col: int) -> None:
    col &= 0x0F
    o = (x + y * fb.stride) >> 1

    if x % 2:
        fb.buf[o] = (col & 0x0F) | (fb.buf[o] & 0xF0)
    else:
        fb.buf[o] = (col << 4) | (fb.buf[o] & 0x0F)


def _getpixel(fb: "FrameBuffer", x: int, y: int) -> int:
    if x % 2:
        return fb.buf[(x + y * fb.stride) >> 1] & 0x0F
    else:
        return fb.buf[(x + y * fb.stride) >> 1] >> 4


def _fill_rect(fb: "FrameBuffer", x: int, y: int, w: int, h: int, col: int) -> None:
    col &= 0x0F
    # uint8_t *pixel_pair = &((uint8_t *)fb->buf)[(x + y * fb->stride) >> 1];
    o = (x + y * fb.stride) >> 1
    col_shifted_left = col << 4
    col_pixel_pair = col_shifted_left | col
    pixel_count_till_next_line = (fb.stride - w) >> 1
    odd_x = x % 2

    for _ in range(h):
        ww = w

        if odd_x and ww > 0:
            fb.buf[o] = (fb.buf[o] & 0xF0) | col
            o += 1
            ww += 1

        # memset(pixel_pair, col_pixel_pair, ww >> 1)
        fb.buf[o : o + col_pixel_pair] = [ww >> 1] * col_pixel_pair
        o += ww >> 1

        if ww % 2:
            fb.buf[o] = col_shifted_left | (fb.buf[o] & 0x0F)
            if not odd_x:
                o += 1

        o += pixel_count_till_next_line


__all__ = ("decorate_gs4_hmsb",)
