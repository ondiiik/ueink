# MicroPython EInk displays drivers
#
# Driver WaveShare 3-color display
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

from struct import pack
from time import sleep


class DrvWaveShare3Color:
    def _init(self) -> None:
        logger.info("\tInit ...")

        with self._rst:
            sleep(0.2)
        sleep(0.2)

        self._cmd(0x06, b"\x17\x17\x17")
        self._cmd(0x00, b"\x0F")
        self._cmd(0x61, pack(">HH", self._w, self._h))
        self._cmd(0x50, b"\xF7")
        self._cmd(0x04)
        self._wait4ready(False)

    def _flush(self) -> None:
        logger.info("\tPower on screen screen ...")
        self._cmd(0x12)
        self._wait4ready(False, 30)

        logger.info("\tPower off screen screen ...")
        self._cmd(0x10, b"\x01")


__all__ = ("DrvWaveShare3Color",)
