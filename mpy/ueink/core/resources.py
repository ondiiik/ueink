# MicroPython EInk displays drivers
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

EPD_GS4_LUT_VCOM = (
    b"\x00\x0A\x00\x00\x00\x01"  # GND 10 |
    b"\x60\x14\x14\x00\x00\x01"  # VDH 20 | VDL 20
    b"\x00\x14\x00\x00\x00\x01"  # GND 20 |
    b"\x00\x13\x0A\x01\x00\x01"  # GND 19 | GND 10
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
)

EPD_GS4_LUT_W2W = (
    b"\x40\x0A\x00\x00\x00\x01"  # VDH 10 |
    b"\x90\x14\x14\x00\x00\x01"  # VDL 20 | VDH 20
    b"\x10\x14\x0A\x00\x00\x01"  # GND 20 | VDH 10
    b"\xA0\x13\x01\x00\x00\x01"  # VDL 19 | VDL 1
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
)

EPD_GS4_LUT_K2W = (
    b"\x40\x0A\x00\x00\x00\x01"  # VDH 10 |
    b"\x90\x14\x14\x00\x00\x01"  # VDL 20 | VDH 20
    b"\x00\x14\x0A\x00\x00\x01"  # ...
    b"\x99\x0C\x01\x03\x04\x01"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
)

EPD_GS4_LUT_W2K = (
    b"\x40\x0A\x00\x00\x00\x01"
    b"\x90\x14\x14\x00\x00\x01"
    b"\x00\x14\x0A\x00\x00\x01"
    b"\x99\x0B\x04\x04\x01\x01"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
)

EPD_GS4_LUT_K2K = (
    b"\x80\x0A\x00\x00\x00\x01"
    b"\x90\x14\x14\x00\x00\x01"
    b"\x20\x14\x0A\x00\x00\x01"
    b"\x50\x13\x01\x00\x00\x01"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
    b"\x00\x00\x00\x00\x00\x00"
)


__all__ = (
    "EPD_GS4_LUT_K2K",
    "EPD_GS4_LUT_K2W",
    "EPD_GS4_LUT_VCOM",
    "EPD_GS4_LUT_W2K",
    "EPD_GS4_LUT_W2W",
)
