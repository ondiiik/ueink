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

from .drv_despi_c02 import DrvDespiC02
from .drv_ws_3c import DrvWaveShare3Color
from .drv_ws_bw import DrvWaveShareBw
from .gpio import NCSPin
from .logging import logger
from .transform import Transform1B, Transform2B

from asyncio import sleep as asleep
from framebuf import FrameBuffer, GS4_HMSB
from gc import collect
from io import BytesIO
from time import sleep
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
        spi: (
            "machine.SPI" | None
        ) = None,  # No SPI in the case that we use driver only as an RAW data generator
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
        self._rotate = 0

        self._blk_size = 1024

        self._flushing = False

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
    def rotate(self) -> int:
        """Gets/sets display rotation

        Display can be rotated by 0, 90, 180 or 270 degrees. When display is rotated
        to different angle then 0 the display flushing is slower as image needs to
        be transformed pixel by pixel before it is flushed.

        When new rotation angle is set, then frame buffer is renew and all already
        written graphics are lost. Any value different from 0, 90, 180, 270 is
        rounded to the nearest valid angle.
        """
        return self._rotate

    @rotate.setter
    def rotate(self, value: int) -> None:
        self._rotate = (((value + 45) // 90) * 90) % 360
        self.width = self._h if self.transposed else self._w
        self.height = self._w if self.transposed else self._h

        if self._fb is not None:
            self._renewfb()

        collect()

    @property
    def transposed(self) -> bool:
        """Gets/sets display transposed state

        When display is transposed, then display frame buffer is rotated either by 90 or
        270 degrees. In this mode the display flushing is slower as the image needs
        to be transformed pixel by pixel before it is flushed.

        When `transposed` is set to `True`, then display angle is set on 90 degrees,
        otherwise to 0 degrees. New transpose value also renew frame buffer, so all
        already written graphics are lost.
        """
        return self._rotate in (90, 270)

    @transposed.setter
    def transposed(self, value: bool) -> None:
        self._rotate = 90 if value else 0
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
        self._flush_raw(self._preflush(stream))

    async def flush_async(
        self, stream: "uio.FileIO" | "uio.BytesIO" | None = None
    ) -> None:
        """Async variant of flush RAW buffers to EInk display

        This method reads RAW data to be displayed on EInk display directly
        from stream. This is fastest and lowest RAM consumption way how to
        write data to eink, where image can be uploaded e.g. directly
        from SD Card (even from zlib compressed form through
        `deflate.DeflateIO`).

        When stream argument is omitted (or is set to `None`), then internal frame
        buffer is used.

        This method is needed as flush procedure usually takes some time when we
        don't want to block other `asyncio` tasks.

        :param stream:    Stream as source of RAW data.
        """
        await self._flush_raw_async(self._preflush(stream))

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
            cls.dim = width, height
            cls._w = width
            cls._h = height
            cls._fb_len = (width * height + 1) // 2
            return cls

        return decorator

    @staticmethod
    def driver_waveshare_black_and_white(cls: type) -> type:
        """Decorator setting methods used for accessing EInk through WaveShare Black & White driver"""
        cls._init = DrvWaveShareBw._init
        cls._flush = DrvWaveShareBw._flush
        cls._flush_async = DrvWaveShareBw._flush_async
        cls._flush_raw_buffers = Transform1B._flush_raw_buffers
        cls._fb2raw = Transform1B._fb2raw
        return cls

    @staticmethod
    def driver_waveshare_3color(cls: type) -> type:
        """Decorator setting methods used for accessing EInk through WaveShare 3-colors driver"""
        cls._init = DrvWaveShare3Color._init
        cls._flush = DrvWaveShare3Color._flush
        cls._flush_async = DrvWaveShare3Color._flush_async
        cls._flush_raw_buffers = Transform2B._flush_raw_buffers
        cls._fb2raw_com = Transform2B._fb2raw_com
        cls._fb2raw = Transform2B._fb2raw_3c
        return cls

    @staticmethod
    def driver_despi_c02(cls: type) -> type:
        """Decorator setting methods used for accessing EInk through DESPI-C02 driver"""
        cls._init = DrvDespiC02._init
        cls._flush = DrvDespiC02._flush
        cls._flush_async = DrvDespiC02._flush_async
        cls._flush_raw_buffers = Transform2B._flush_raw_buffers
        cls._fb2raw_com = Transform2B._fb2raw_com
        cls._fb2raw = Transform2B._fb2raw_gs
        return cls

    # #################################
    # ###  Internal helpers methods ###
    # #################################
    def _mkfb(self) -> None:
        if self._fb is None:
            self._renewfb()

    def _renewfb(self) -> None:
        l = (self.width * self.height + 1) // 2
        logger.info(f"New frame buffer: {self.width} x {self.height} ({l} bytes)")

        if self._buf is None:
            self._buf = bytearray(l)
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

    def _wait4ready(self, busy: bool, timeout: int = 10) -> None:
        rdy = int(not busy)
        for _ in range(timeout * 100):
            if rdy == self._busy.value():
                return
            sleep(0.01)

        raise RuntimeError("EPD Timeout")

    async def _wait4ready_async(self, busy: bool, timeout: int = 10) -> None:
        rdy = int(not busy)
        for _ in range(timeout * 100):
            if rdy == self._busy.value():
                return
            await asleep(0.01)

        raise RuntimeError("EPD Timeout")

    def _preflush(self, stream: "uio.FileIO" | "uio.BytesIO" | None = None) -> None:
        if self._spi is None:
            raise RuntimeError("Flush is not supported when no SPI bus selected")

        if stream is None:
            if self._fb is None:
                raise RuntimeError(
                    "Frame buffer was not created (property Eink.fb was not read)"
                )
            stream = BytesIO(self._fb2raw())

        return stream

    def _flush_raw(self, stream: "uio.FileIO" | "uio.BytesIO") -> None:
        if self._flushing:
            raise RuntimeError("EInk is already flushing by someone else")

        logger.info("Display frame:")
        self._init()
        self._flush_raw_buffers(stream)
        self._flush()

    async def _flush_raw_async(self, stream: "uio.FileIO" | "uio.BytesIO") -> None:
        if self._flushing:
            raise RuntimeError("EInk is already flushing by someone else")

        self._flushing = True
        try:
            logger.info("Display frame:")
            self._init()
            self._flush_raw_buffers(stream)
            await self._flush_async()
        finally:
            self._flushing = False


__all__ = ("IEpd",)
