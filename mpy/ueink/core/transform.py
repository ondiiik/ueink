from __future__ import annotations

from .logging import logger

from framebuf import FrameBuffer, MONO_HLSB


class Transform1B:
    def _fb2raw(self) -> bytearray:
        raw_buf = bytearray(self._fb_len // 4)

        if self._tran:
            # Transposing display orientation. Pixel by pixel - slow method
            px_i = self._fb.pixel
            px_o = FrameBuffer(raw_buf, self.height, self.width, MONO_HLSB).pixel
            r = self.height - 1

            for y in range(self.width):
                for x in range(self.height):
                    px_o(x, y, px_i(y, r - x) >> 3)
        else:
            # Use of built-in blit conversion (native display orientation)
            fb = FrameBuffer(raw_buf, self.width, self.height, MONO_HLSB)
            pal = FrameBuffer(bytearray(b"\x00\xFF"), 16, 1, MONO_HLSB)
            fb.blit(self._fb, 0, 0, -1, pal)

        return raw_buf

    def _flush_raw_buffers(self, stream: "uio.FileIO" | "uio.BytesIO") -> None:
        buf_len = self._fb_len // 4
        logger.info(f"\tWrite RAW buffer ({buf_len} bytes) ...")
        segm_len = min(buf_len, self._blk_size)
        segm = memoryview(bytearray(segm_len))

        self._cmd(0x24)
        cnt = stream.readinto(segm)
        while cnt:
            self._data(segm[:cnt])
            cnt = stream.readinto(segm)


class Transform2B:
    def _fb2raw_gs(self) -> bytearray:
        return self._fb2raw_com(b"\x00\xFF", b"\x0F\x0F")

    def _fb2raw_3c(self) -> bytearray:
        return self._fb2raw_com(b"@\x00", b"\xC0\x00")

    def _fb2raw_com(self, pal1: bytes, pal2: bytes) -> bytearray:
        raw_buf = memoryview(bytearray(self._fb_len // 2))
        buf_len = self._fb_len // 4
        pal1 = FrameBuffer(bytearray(pal1), 16, 1, MONO_HLSB)
        pal2 = FrameBuffer(bytearray(pal2), 16, 1, MONO_HLSB)

        if self._tran:
            # Transposing display orientation. Pixel by pixel - slow method
            px_i = self._fb.pixel
            px_o1 = FrameBuffer(raw_buf[:buf_len], self._w, self._h, MONO_HLSB).pixel
            px_o2 = FrameBuffer(raw_buf[buf_len:], self._w, self._h, MONO_HLSB).pixel
            r = self._h - 1

            pal1 = pal1.pixel
            pal2 = pal2.pixel
            for y in range(self._h):
                for x in range(self._w):
                    p = px_i(r - y, x)
                    px_o1(x, y, pal1(p, 0))
                    px_o2(x, y, pal2(p, 0))
        else:
            # Direct frame buffer conversion (native display orientation)
            fb = FrameBuffer(raw_buf[:buf_len], self.width, self.height, MONO_HLSB)
            fb.blit(self._fb, 0, 0, -1, pal1)

            fb = FrameBuffer(raw_buf[buf_len:], self.width, self.height, MONO_HLSB)
            fb.blit(self._fb, 0, 0, -1, pal2)

        return raw_buf

    def _flush_raw_buffers(self, stream: "uio.FileIO" | "uio.BytesIO") -> None:
        logger.info("\tWrite RAW buffer 1 ...")
        buf_len = self._fb_len // 4
        segm_len = min(buf_len, self._blk_size)
        segm = memoryview(bytearray(segm_len))

        self._cmd(0x10)
        for i in range(0, buf_len, segm_len):
            cnt = stream.readinto(segm[: min(segm_len, buf_len - i)])
            self._data(segm[:cnt])

        logger.info("\tWrite RAW buffer 2 ...")
        self._cmd(0x13)
        for i in range(0, buf_len, segm_len):
            cnt = stream.readinto(segm[: min(segm_len, buf_len - i)])
            self._data(segm[:cnt])


__all__ = (
    "Transform1B",
    "Transform2B",
)
