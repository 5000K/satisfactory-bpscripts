import struct


class BufferReader:
    def __init__(self, buffer):
        self.buffer = buffer
        self.offset = 0

    def print_offset_hex(self):
        print(f"Offset: {self.offset} (0x{self.offset:02X})")

    def next_byte(self):
        byte = self.buffer[self.offset]
        self.offset += 1
        return byte

    def next_float(self):
        b = self.next_bytes(4)
        val = struct.unpack("f", b)
        return val[0]

    def next_int32(self):
        value = int.from_bytes(self.buffer[self.offset:self.offset+4], byteorder='little')
        self.offset += 4
        return value

    def next_int64(self):
        value = int.from_bytes(self.buffer[self.offset:self.offset+8], byteorder='little')
        self.offset += 8
        return value

    def next_string(self):
        length = self.next_int32()

        value: str = self.buffer[self.offset:self.offset+length].decode("utf-8")
        self.offset += length
        return value.strip("\x00")

    def next_bytes(self, length):
        value = self.buffer[self.offset:self.offset+length]
        self.offset += length
        return value

    def skip_forward(self, offset):
        self.offset += offset

    def skip_backwards(self, offset):
        self.offset -= offset

    def set_offset(self, offset):
        self.offset = offset

    def set_jump_point(self) -> callable:
        offset = self.offset
        return lambda: self.set_offset(offset)
