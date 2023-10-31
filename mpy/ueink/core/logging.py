from __future__ import annotations


from .config import epd_global_params


class logger:
    @staticmethod
    def info(*args) -> None:
        if not epd_global_params["silent"]:
            print("eink ::", *args)


__all__ = ("logger",)
