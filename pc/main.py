from __future__ import annotations

from ueink import epd_global_params
from ueink.epd_gdey075t7 import EpdRaw

from machine import Pin, SPI
from os import mount
from sdcard import SDCard

epd_global_params["epd_segment_size"] = 1024

spi = SPI(1)
mount(SDCard(spi, Pin(15)), "/sd")

epd = EpdRaw(spi=spi, cs=Pin(16), dc=Pin(4), rst=Pin(2), busy=Pin(5))

with open("/sd/test.raw", "rb") as f:
    epd.flush_raw(f)


__all__ = (
    "epd",
    "spi",
)
