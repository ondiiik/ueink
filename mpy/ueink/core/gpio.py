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

from machine import Pin


class NCSPin:
    def __init__(self, pin: Pin) -> None:
        pin.init(pin.OUT, value=True)
        self._pin = pin

    def __enter__(self) -> NCSPin:
        self._pin(False)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._pin(True)


class CSPin:
    def __init__(self, pin: Pin) -> None:
        pin.init(pin.OUT, value=False)
        self._pin = pin

    def __enter__(self) -> CSPin:
        self._pin(True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._pin(False)


__all__ = (
    "CSPin",
    "NCSPin",
)
