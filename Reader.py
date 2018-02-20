# -*- coding: utf-8 -*-

from io import BufferedReader, BytesIO


class BinaryReader(BufferedReader):

    def __init__(self, stream):
        super().__init__(BytesIO(stream))

    def read_uint32(self):
        return int.from_bytes(self.read(4), 'little')

    def read_uint16(self):
        return int.from_bytes(self.read(2), 'little')

    def read_int16(self):
        return int.from_bytes(self.read(2), 'little', signed=True)

    def read_byte(self):
        return int.from_bytes(self.read(1), 'little')

    def read_string(self, length):
        return self.read(length).decode('utf-8')
