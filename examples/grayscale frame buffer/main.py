from __future__ import annotations

from ueink import epd_global_params
from ueink.epd_gdey075t7 import Epd  # Choose your display (GDEY075T7 in this case)

from machine import Pin, SPI
from random import randint


epd_global_params["silent"] = False


# Draw something on EPD screen (into frame buffer)
def draw(epd, title) -> None:
    fb = epd.fb

    print("Drawing ...")

    print("\tdraw title")
    o = 30
    x = (epd.width - 8 * len(title)) // 2
    fb.rect(0, 0, epd.width, o, epd.color["black"], True)
    fb.text(title, x + 1, o // 2 - 3, 6)
    fb.text(title, x, o // 2 - 4, epd.color["white"])

    print("\tdraw palete")
    o += 4
    m = epd.width - 20
    n = m // 16
    h = 80
    y = 165 + o
    for c, x in enumerate(range(10, m - n, n)):
        fb.rect(x, y, n, h, c, True)
        q = x + n
    fb.rect(10, y, 16 * n, h, epd.color["black"])

    print("\tdraw text intensity")
    for c in range(16):
        if c > 11:
            fb.rect(10, o + 10 * c - 1, q - 10, 10, 11, True)
        fb.text(f"Hello display ;-) - color {c}", 20, o + 10 * c, c)

    print("\tdraw random lines")
    for _ in range(1000):
        fb.line(
            randint(10, q - 10),
            randint(y + h + 10, epd.height - 10),
            randint(10, q - 10),
            randint(y + h + 10, epd.height - 10),
            randint(0, 15),
        )


# Use your own SPI settings and create display driver
print("Building EPD driver ...")
epd = Epd(spi=SPI(2), cs=Pin(39), dc=Pin(40), rst=Pin(41), busy=Pin(42))

# Create frame buffer
print("Building frame buffer ...")
fb = epd.fb

# Draw something
print("Drawing ...")
draw(epd, "Full screen drawing")

# Flush the result on display
print("Flushing the screen ...")
epd.flush()

print("That's it ;-)")


__all__ = (
    "draw",
    "epd",
    "fb",
)
