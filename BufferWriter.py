import struct
from typing import Callable


class BufferWriter:
    def __init__(self):
        self.buffer = bytearray()

    def reserve_write_length_padded(self) -> Callable[[], callable]:
        """Reserve space for the length of a property that will be written later.

        Assumes the property might be written with a padding, only measuring after the padding.
        :return: A function that will write the length of the property to the reserved space.
        """

        offset = len(self.buffer)
        self.buffer.extend(b"\x00" * 4)
        written = False

        def inner():
            data_offset = len(self.buffer)

            def write():
                nonlocal written
                if not written:
                    length = data_offset - (offset + 4)
                    val = length.to_bytes(4, byteorder='little', signed=True)
                    self.buffer[offset:offset+4] = val
                    written = True

            return write

        return inner

    def next_byte(self, v: int):
        self.buffer.append(v)

    def next_float(self, v: float):
        val = struct.pack("f", v)
        self.buffer.extend(val)

    def next_int32(self, v: int):
        val = v.to_bytes(4, byteorder='little', signed=True)
        self.buffer.extend(val)

    def next_int64(self, v: int):
        val = v.to_bytes(8, byteorder='little', signed=True)
        self.buffer.extend(val)

    def next_string(self, v: str):
        v += "\x00"
        val = v.encode("utf-8")
        self.next_int32(len(val))
        self.buffer.extend(val)

    def next_guid(self, guid: bytes):  # 16 byte guid
        self.buffer.extend(guid)

    def next_bytes(self, b: bytes):
        self.buffer.extend(b)