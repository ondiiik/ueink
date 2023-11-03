# MicroPython EInk displays drivers
#
# Driver DESPI C02
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

from .logging import logger
from .resources import (
    EPD_GS4_LUT_K2K,
    EPD_GS4_LUT_K2W,
    EPD_GS4_LUT_VCOM,
    EPD_GS4_LUT_W2K,
    EPD_GS4_LUT_W2W,
)

from struct import pack
from time import sleep


class DrvDespiC02:
    def _init(self) -> None:
        logger.info("\tInit ...")

        with self._rst:
            sleep(0.01)
        sleep(0.01)

        self._cmd(0x01, b"\x07\x07\x3F\x3F\x00")
        self._cmd(0x06, b"\x17\x17\x28\x17")
        self._cmd(0x00, b"\x3F")
        self._cmd(0x61, pack(">HH", self._w, self._h))
        self._cmd(0x15, b"\x00")
        self._cmd(0x82, b"\x30")
        self._cmd(0x50, b"\x29\x07")
        self._cmd(0x60, b"\x22")
        self._cmd(0x92)

        self._cmd(0x20, EPD_GS4_LUT_VCOM)
        self._cmd(0x21, EPD_GS4_LUT_W2W)
        self._cmd(0x22, EPD_GS4_LUT_K2W)
        self._cmd(0x23, EPD_GS4_LUT_W2K)
        self._cmd(0x24, EPD_GS4_LUT_K2K)

        self._cmd(0x04)
        self._wait4ready(False)

    def _flush(self) -> None:
        logger.info("\tFlush screen ...")
        self._cmd(0x12)
        sleep(0.002)
        self._wait4ready(False)

        logger.info("\tPower off screen screen ...")
        self._cmd(0x50, b"0xF7")
        self._cmd(0x02)
        self._wait4ready(False)
        sleep(0.1)
        self._cmd(0x07, b"0xA5")


__all__ = ("DrvDespiC02",)
