# MicroPython EInk displays drivers
#
# Driver WaveShare Black & White
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
from .resources import EPD_WS_BW

from struct import pack
from time import sleep


class DrvWaveShareBw:
    def _init(self) -> None:
        logger.info("\tInit ...")

        sleep(0.02)
        with self._rst:
            sleep(0.005)
        sleep(0.021)
        self._wait4ready(True)

        self._cmd(0x12)
        self._wait4ready(True)

        self._cmd(0x01, b"\xC7\x00\x01")
        self._cmd(0x11, b"\x01")
        self._cmd(0x44, pack("<bb", 0, (self._w - 1) >> 3))
        self._cmd(0x45, pack("<HH", (self._h - 1), 0))
        self._cmd(0x3C, b"\x01")
        self._cmd(0x18, b"\x80")
        self._cmd(0x22, b"\xB1")
        self._cmd(0x20)
        self._cmd(0x4E, b"\x00")
        self._cmd(0x4F, pack("<H", (self._h - 1)))
        self._wait4ready(True)

        lut = memoryview(EPD_WS_BW)

        self._cmd(0x32, lut)
        self._wait4ready(True)

        self._cmd(0x3F, lut[153:154])
        self._cmd(0x03, lut[154:155])
        self._cmd(0x04, lut[155:158])
        self._cmd(0x2C, lut[158:159])

    def _flush(self) -> None:
        logger.info("\tPower on screen screen ...")
        self._cmd(0x22, b"\xC7")
        self._cmd(0x20)
        self._wait4ready(True)

        logger.info("\tPower off screen screen ...")
        self._cmd(0x10, b"\x01")


__all__ = ("DrvWaveShareBw",)
