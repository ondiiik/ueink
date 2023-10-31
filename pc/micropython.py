from __future__ import annotations


def native(fn) -> None:
    return fn


def const(v) -> None:
    return v


__all__ = (
    "const",
    "native",
)
