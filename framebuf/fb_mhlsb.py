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


def decorate_mhlsb(fb: "FrameBuffer") -> None:
    fb._getpixel = _getpixel
    fb._setpixel = _setpixel
    fb._fill_rect = _fill_rect


def _setpixel(fb: "FrameBuffer", x: int, y: int, col: int) -> None:
    index = (x + y * fb.stride) >> 3
    offset = 7 - (x & 0x07)
    fb.buf[index] = (fb.buf[index] & ~(0x01 << offset)) | ((col != 0) << offset)


def _getpixel(fb: "FrameBuffer", x: int, y: int) -> int:
    index = (x + y * fb.stride) >> 3
    offset = 7 - (x & 0x07)
    return (fb.buf[index] >> (offset)) & 0x01


def _fill_rect(fb: "FrameBuffer", x: int, y: int, w: int, h: int, col: int) -> None:
    advance = fb.stride >> 3
    for _ in range(w):
        o = (x >> 3) + y * advance
        offset = 7 - (x & 0x07)
        for _ in range(h):
            fb.buf[o] = (fb.buf[o] & ~(0x01 << offset)) | ((col != 0) << offset)
            b += advance
        x += 1


__all__ = ("decorate_mhlsb",)
