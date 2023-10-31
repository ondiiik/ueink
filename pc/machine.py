from __future__ import annotations


class Pin:
    OUT = 12
    IN = 21

    def __init__(self, *args, **kw) -> None:
        ...

    def __call__(self, v) -> None:
        ...

    def init(self, *args, **kw) -> None:
        ...

    def value(self, v=None) -> None:
        return 1


class SPI:
    def __init__(self, *args, **kw) -> None:
        ...

    def init(self, *args, **kw) -> None:
        ...

    def write(self, b) -> None:
        ...


__all__ = (
    "Pin",
    "SPI",
)
