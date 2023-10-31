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

from .gpio import NCSPin
from .logging import logger

from framebuf import FrameBuffer, GS4_HMSB, MONO_HLSB
from gc import collect
from io import BytesIO
from upycompat.abc import (
    ABC,
    abstractmethod,
)


class IEpd(ABC):
    """Base interface for EPD drivers

    Interface represents abstraction for EInk driver. This driver is always based on SPI
    BUS, however it can be also used just for conversion from frame buffer to display
    RAW data (without SPI).

    :param spi:    Either object of `machine.SPI` used for communication with EInk display
                   or `None` when driver is used just for frame buffer to RAW conversion.
    :param cs:     Chip Select pin of EInk display (relevant only when `spi` is not `None`)
    :param dc:     Data/Command pin of EInk display (relevant only when `spi` is not `None`)
    :param rst:    Reset pin of EInk display (relevant only when `spi` is not `None`)
    :param busy:   Busy signalization pin of EInk display (relevant only when `spi` is not `None`)
    """

    def __init__(
        self,
        *,
        spi: "machine.SPI"
        | None = None,  # No SPI in the case that we use driver only as an RAW data generator
        cs: "machine.Pin" | None = None,
        dc: "machine.Pin" | None = None,
        rst: "machine.Pin" | None = None,
        busy: "machine.Pin" | None = None,
    ) -> None:
        self._spi = spi

        if spi is not None:
            self._spi.init(
                baudrate=2000000,
                polarity=0,
                phase=0,
            )
            logger.info("\tSPI - [ OK ]")

            self._cs = cs
            self._dc = dc
            self._rst = rst
            self._busy = busy

            if cs:
                self._cs = NCSPin(cs)

            if dc:
                self._dc.init(self._dc.OUT, value=0)

            if rst:
                self._rst = NCSPin(rst)

            if busy:
                self._busy.init(self._busy.IN)

            logger.info("\tPins - [ OK ]")
        else:
            logger.info("\tSPI - [ unused ]")

        self._fb = None
        self._buf = None
        self._tran = False

        self._blk_size = 1024

        self.width = self._w
        self.height = self._h

    # ##########################
    # ###  Abstract methods  ###
    # ##########################
    @abstractmethod
    def _init(self) -> None:
        """Interface method which proceed complete initialization of EInk"""
        ...

    @abstractmethod
    def _flush_raw(self, stream: "uio.FileIO" | "uio.BytesIO") -> None:
        """Interface method for flushing RAW buffers to EInk display

        This method reads RAW data to be displayed on EInk display directly
        from stream. RAW data are specific for each type of EInk display.

        :param stream:    Stream as source of RAW data.
        """
        ...

    @abstractmethod
    def _fb2raw(self) -> bytearray:
        """Interface method for building of display RAW data from buffer buffer
        :return:    EInk RAW data frame representation
        """
        ...

    # ###################
    # ###  Properties ###
    # ###################
    @property
    def fb(self) -> FrameBuffer:
        """Gets frame buffer usable for drawing into selected viewport"""
        self._mkfb()
        return self._fb

    @property
    def buf(self) -> bytearray:
        """Gets byte array representation of frame buffer usable for drawing into selected viewport"""
        self._mkfb()
        return self._buf

    @property
    def raw(self) -> bytearray:
        """Gets frame buffer converted to display native RAW format

        Just note that this calls conversion which may take some time, however it can be used to get
        native RAW format of selected display which can be stored to file system or sent to another
        device through Ethernet.
        """
        self._mkfb()
        return self._fb2raw()

    @property
    def copy_block_size(self) -> int:
        """Gets/sets block size used for RAW copy of data to display

        This size is 1KB by default. It can be increased to make data transfer slightly faster
        or decreased to save a bit more RAM.
        """
        return self._blk_size

    @copy_block_size.setter
    def copy_block_size(self, value: int) -> None:
        self._blk_size = value

    @property
    def transposed(self) -> bool:
        """Gets/sets display transposed state

        When display is transposed, then display frame buffer is rotated 90 degrees.
        in this mode the display flushing is slower as image needs to be transposed
        before it is flushed.
        """
        return self._tran

    @transposed.setter
    def transposed(self, value: bool) -> None:
        self._tran = value
        self.width = self._h if value else self._w
        self.height = self._w if value else self._h

        if self._fb is not None:
            self._renewfb()

        collect()

    # #####################
    # ###  Base methods ###
    # #####################
    def flush(self, stream: "uio.FileIO" | "uio.BytesIO" | None = None) -> None:
        """Flush RAW buffers to EInk display

        This method reads RAW data to be displayed on EInk display directly
        from stream. This is fastest and lowest RAM consumption way how to
        write data to eink, where image can be uploaded e.g. directly
        from SD Card (even from zlib compressed form through
        `deflate.DeflateIO`).

        When stream argument is omitted (or is set to `None`), then internal frame
        buffer is used.

        :param stream:    Stream as source of RAW data.
        """
        if self._spi is None:
            raise RuntimeError("Flush is not supported when no SPI bus selected")

        if stream is None:
            if self._fb is None:
                raise RuntimeError(
                    "Frame buffer was not created (property Eink.fb was not read)"
                )
            stream = BytesIO(self._fb2raw())

        self._flush_raw(stream)

    # ###################
    # ###  Decorators ###
    # ###################
    @staticmethod
    def parameters(
        *,
        width: int,
        height: int,
        colors: dict,
    ) -> "function":
        """Decorator helping to preset specific type of EInk display

        :param width:        Define display width
        :param height:       Define display height
        """

        def decorator(cls: type) -> type:
            cls.color = colors
            cls._w = width
            cls._h = height
            cls._fb_len = (width * height + 1) // 2
            return cls

        return decorator

    @staticmethod
    def two_buffers_grayscale(cls: type) -> type:
        """Decorator setting methods used to decode and write gray-scale data to double buffered system"""
        cls._flush_raw_buffers = cls._2b_flush
        cls._fb2raw = cls._2b_fb2raw_gs
        return cls

    # #################################
    # ###  Internal helpers methods ###
    # #################################
    def _mkfb(self) -> None:
        if self._fb is None:
            self._renewfb()

    def _renewfb(self) -> None:
        if self._buf is None:
            self._buf = bytearray((self.width * self.height + 1) // 2)
        self._fb = FrameBuffer(self._buf, self.width, self.height, GS4_HMSB)
        self._fb.fill(self.color["white"])

    def _cmd(self, command, data=None) -> None:
        self._dc(0)
        with self._cs:
            self._spi.write(bytearray([command]))
        if data is not None:
            self._data(data)

    def _data(self, data) -> None:
        self._dc(1)
        with self._cs:
            self._spi.write(data)

    def _2b_fb2raw_gs(self) -> bytearray:
        raw_buf = memoryview(bytearray(self._fb_len // 2))
        buf_len = self._fb_len // 4

        if self._tran:
            # Transposing display orientation. Pixel by pixel - slow method
            fb = self._fb
            px_in = fb.pixel
            px_o1 = FrameBuffer(
                raw_buf[:buf_len], self.height, self.width, MONO_HLSB
            ).pixel
            px_o2 = FrameBuffer(
                raw_buf[buf_len:], self.height, self.width, MONO_HLSB
            ).pixel
            r = self.height - 1

            for y in range(self.width):
                for x in range(self.height):
                    p = px_in(y, r - x) >> 2
                    px_o1(x, y, p >> 1)
                    px_o2(x, y, p & 1)
        else:
            # Direct frame buffer conversion (native display orientation)
            self._2b_convert(
                raw_buf[:buf_len],
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x01\x01\x01\x01\x01\x01\x01\x02\x02\x02\x02\x02\x02\x02\x02\x03\x03\x03\x03\x03\x03\x03\x03\x02\x02\x02\x02\x02\x02\x02\x02\x03\x03\x03\x03\x03\x03\x03\x03\x02\x02\x02\x02\x02\x02\x02\x02\x03\x03\x03\x03\x03\x03\x03\x03\x02\x02\x02\x02\x02\x02\x02\x02\x03\x03\x03\x03\x03\x03\x03\x03\x02\x02\x02\x02\x02\x02\x02\x02\x03\x03\x03\x03\x03\x03\x03\x03\x02\x02\x02\x02\x02\x02\x02\x02\x03\x03\x03\x03\x03\x03\x03\x03\x02\x02\x02\x02\x02\x02\x02\x02\x03\x03\x03\x03\x03\x03\x03\x03\x02\x02\x02\x02\x02\x02\x02\x02\x03\x03\x03\x03\x03\x03\x03\x03",
            )

            self._2b_convert(
                raw_buf[buf_len:],
                b"\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01\x02\x02\x02\x02\x03\x03\x03\x03\x02\x02\x02\x02\x03\x03\x03\x03\x02\x02\x02\x02\x03\x03\x03\x03\x02\x02\x02\x02\x03\x03\x03\x03\x02\x02\x02\x02\x03\x03\x03\x03\x02\x02\x02\x02\x03\x03\x03\x03\x02\x02\x02\x02\x03\x03\x03\x03\x02\x02\x02\x02\x03\x03\x03\x03\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01\x00\x00\x00\x00\x01\x01\x01\x01\x02\x02\x02\x02\x03\x03\x03\x03\x02\x02\x02\x02\x03\x03\x03\x03\x02\x02\x02\x02\x03\x03\x03\x03\x02\x02\x02\x02\x03\x03\x03\x03\x02\x02\x02\x02\x03\x03\x03\x03\x02\x02\x02\x02\x03\x03\x03\x03\x02\x02\x02\x02\x03\x03\x03\x03\x02\x02\x02\x02\x03\x03\x03\x03",
            )

        return raw_buf

    def _2b_convert(self, raw_buf: memoryview, lut: dict) -> None:
        s = 0
        for d in range(len(raw_buf)):
            b = 0
            for _ in range(4):
                b <<= 2
                b |= lut[self._buf[s]]
                s += 1
            raw_buf[d] = b

    def _2b_flush(self, stream: "uio.FileIO" | "uio.BytesIO") -> None:
        logger.info("\tWrite RAW buffer 1 ...")
        buf_len = self._fb_len // 4
        segm_len = min(buf_len, self._blk_size)
        segm = memoryview(bytearray(segm_len))

        self._cmd(0x10)
        for i in range(0, buf_len, segm_len):
            cnt = stream.readinto(segm[: min(segm_len, buf_len - i)])
            self._data(segm[:cnt])

        logger.info("\tWrite RAW buffer 2 ...")
        self._cmd(0x13)
        for i in range(0, buf_len, segm_len):
            cnt = stream.readinto(segm[: min(segm_len, buf_len - i)])
            self._data(segm[:cnt])


__all__ = ("IEpd",)
