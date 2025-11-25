from __future__ import annotations

from machine import PWM, Pin
import re
from time import sleep_ms, ticks_diff, ticks_ms


class Beeper:
    _scale = b"\x00\x83\x00\x8b\x00\x93\x00\x9c\x00\xa5\x00\xaf\x00\xb9\x00\xc4\x00\xd0\x00\xdc\x00\xe9\x00\xf7\x01\x06\x01\x15\x01&\x017\x01J\x01]\x01r\x01\x88\x01\x9f\x01\xb8\x01\xd2\x01\xee\x02\x0b\x02*\x02K\x02n\x02\x93\x02\xba\x02\xe4\x03\x10\x03>\x03p\x03\xa4\x03\xdc"
    _note2idx = {
        "c": 0,
        "c#": 1,
        "d": 2,
        "d#": 3,
        "e": 4,
        "f": 5,
        "f#": 6,
        "g": 7,
        "g#": 8,
        "h": 9,
        "h#": 10,
        "a": 11,
    }
    _re = re.compile("[ \n][ \n]*")

    def __init__(self, pin: Pin) -> None:
        self.volume = 100
        self._pwm = PWM(pin, freq=440, duty=1024)

    def song(self, song: str) -> None:
        song = self._re.split(song)
        print(song)
        tpm = int(song[0])
        tact = round(60000 / tpm)
        for note in song[1:]:
            if note:
                duration, note = note.split("-")
                if note == "p":
                    sleep_ms(round(tact / int(duration)))
                else:
                    self.note(note, round(tact / int(duration)))

    def note(self, note: str, delay: int) -> None:
        note, scale = note[:-1], note[-1]
        idx = (self._note2idx[note] + 12 * int(scale)) * 2
        freq = self._scale[idx] * 256 + self._scale[idx + 1]
        self.tone(freq, delay)

    def tone(self, freq: int, delay: int) -> None:
        start = ticks_ms()

        self._pwm.freq(freq)

        for i in reversed(range(0, 25)):
            if ticks_diff(ticks_ms(), start) > delay:
                break
            self._pwm.duty(1024 - i * self.volume // 100)
            sleep_ms(30)

        self._pwm.duty(1024)

        while ticks_diff(ticks_ms(), start) < delay:
            sleep_ms(10)


__all__ = ("Beeper",)
