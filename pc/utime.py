from __future__ import annotations

from time import *


def sleep_ms(t) -> None:
    sleep(t / 1000)


__all__ = ("sleep_ms",)
