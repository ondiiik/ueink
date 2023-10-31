from __future__ import annotations

from ueink.gpio import CSPin

from machine import Pin, SPI, SoftSPI
from os import mount
from sdcard import SDCard


power_on = CSPin(Pin(14))


def mount_sd() -> None:

    sd_spi = SPI(1)
    sd_cs = Pin(10)
    sd_device = SDCard(sd_spi, sd_cs)

    mount(sd_device, "/sd")


__all__ = (
    "mount_sd",
    "power_on",
)
