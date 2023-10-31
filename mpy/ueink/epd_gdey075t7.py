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

from .core.base import IEpd
from .core.logging import logger
from .core.resources import (
    EPD_GS4_LUT_K2K,
    EPD_GS4_LUT_K2W,
    EPD_GS4_LUT_VCOM,
    EPD_GS4_LUT_W2K,
    EPD_GS4_LUT_W2W,
)

from io import BytesIO
from struct import pack
from time import sleep
from upycompat.typing_extensions import override


@IEpd.parameters(width=800, height=480, colors={"white": 15, "gray": 12, "black": 0})
@IEpd.two_buffers_grayscale
class Epd(IEpd):
    def _init(self) -> None:
        logger.info("\tInit ...")
        self._reset()
        self._setup()
        self._set_lut()

    @override
    def _flush_raw(self, stream: "uio.FileIO" | BytesIO) -> None:
        logger.info("Display frame:")
        self._init()
        self._on()
        self._flush_raw_buffers(stream)
        self._flush()
        self._off()

    def _reset(self) -> None:
        with self._rst:
            sleep(0.01)
        sleep(0.01)

    def _setup(self) -> None:
        self._initialized = True
        self._cmd(0x01, b"\x07\x07\x3F\x3F\x00")
        self._cmd(0x06, b"\x17\x17\x28\x17")
        self._cmd(0x00, b"\x3F")
        self._cmd(0x61, pack("!HH", self._w, self._h))
        self._cmd(0x15, b"\x00")
        self._cmd(0x82, b"\x30")
        self._cmd(0x50, b"\x29\x07")
        self._cmd(0x60, b"\x22")
        self._cmd(0x92)

    def _set_lut(self) -> None:
        self._cmd(0x20, EPD_GS4_LUT_VCOM)
        self._cmd(0x21, EPD_GS4_LUT_W2W)
        self._cmd(0x22, EPD_GS4_LUT_K2W)
        self._cmd(0x23, EPD_GS4_LUT_W2K)
        self._cmd(0x24, EPD_GS4_LUT_K2K)

    def _flush(self) -> None:
        logger.info("\tFlush screen ...")
        self._cmd(0x12)
        sleep(0.002)
        self._wait4ready()

    def _off(self) -> None:
        logger.info("\tPower off screen screen ...")
        self._cmd(0x50, b"0xF7")
        self._cmd(0x02)
        self._wait4ready()
        sleep(0.1)
        self._cmd(0x07, b"0xA5")

    def _on(self) -> None:
        logger.info("\tPower on screen screen ...")
        self._cmd(0x04)
        self._wait4ready()

    def _wait4ready(self) -> None:
        for _ in range(2000):
            if self._busy.value():
                return
            sleep(0.01)

        raise RuntimeError("EPD Timeout")


__all__ = ("Epd",)
