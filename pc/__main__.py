from __future__ import annotations

from ueink import epd_global_params
from ueink.epd_gdey075t7 import Epd

epd_global_params["silent"] = False

epd = Epd()
epd.transposed = True
fb = epd.fb
fb.rect(10, 10, 50, 100, 0, True)
raw = epd.raw

__all__ = (
    "epd",
    "fb",
    "raw",
)
