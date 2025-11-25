from __future__ import annotations

from ueink.epd_gdey075t7 import Epd  # Choose your display (GDEY075T7 in this case)

from machine import Pin, SPI


# Use your own SPI settings and create display driver
print("Building EPD driver ...")
epd = Epd(spi=SPI(2), cs=Pin(39), dc=Pin(40), rst=Pin(41), busy=Pin(42))

# Flush the result on display
# Be sure that RAW data matches exactly to your selected display (GDEY075T7 in this case)
print("Flushing the screen ...")
with open("screen.raw", "rb") as f:
    epd.flush(f)

print("That's it ;-)")


__all__ = ("epd",)
