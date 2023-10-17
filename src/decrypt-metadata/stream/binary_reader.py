# pylint: disable=all

import struct

class BinaryReader:
    def __init__(self, stream, is_little_endian: bool):
        self.stream = stream
        self.offset = 0
        if is_little_endian:
            self.byteorder = "little"
        else:
            self.byteorder = "big"

    def read(self, size):
        data = self.stream[self.offset:self.offset + size]
        self.offset += size
        return data

    def readBool(self):
        return bool(self.read(1)[0])

    def readInt8(self):
        return int.from_bytes(self.read(1), byteorder=self.byteorder, signed=True)

    def readUInt8(self):
        return int.from_bytes(self.read(1), byteorder=self.byteorder, signed=False)

    def readInt16(self):
        return int.from_bytes(self.read(2), byteorder=self.byteorder, signed=True)

    def readUInt16(self):
        return int.from_bytes(self.read(2), byteorder=self.byteorder, signed=False)

    def readInt32(self):
        return int.from_bytes(self.read(4), byteorder=self.byteorder, signed=True)

    def readUInt32(self):
        return int.from_bytes(self.read(4), byteorder=self.byteorder, signed=False)

    def readInt64(self):
        return int.from_bytes(self.read(8), byteorder=self.byteorder, signed=True)

    def readUInt64(self):
        return int.from_bytes(self.read(8), byteorder=self.byteorder, signed=False)

    def readFloat(self):
        return struct.unpack('>f', self.read(4))[0]

    def readDouble(self):
        return struct.unpack('>d', self.read(8))[0]

    def readBoolArray(self):
        length = self.readUInt32()
        return [self.readBool() for _ in range(length)]

    def readInt8Array(self):
        length = self.readUInt32()
        return [self.readInt8() for _ in range(length)]

    def readUInt8Array(self):
        length = self.readUInt32()
        return bytearray(self.read(length))

    def readVarInt(self):
        return NotImplementedError
        # result = 0
        # shift = 0
        # while True:
        #     byte = self.readUInt8()
        #     result |= (byte & 0x7F) << shift
        #     if not byte & 0x80:
        #         if result >= (1 << 63):
        #             result -= (1 << 64)
        #         return result
        #     shift += 7

    def readStringC(self):
        string = b''
        while True:
            char = self.readUInt8()
            if char == 0:
                break
            string += bytes([char])
        return string.decode('utf-8')

    def readStringCArray(self):
        strings = []
        while True:
            string = self.readStringC()
            if not string:
                break
            strings.append(string)
        return strings

    def readString(self, length=None):
        if length is None:
            length = self.readUInt32()
        return self.read(length).decode('utf-8')

    def readStringArray(self):
        length = self.readUInt32()
        return [self.readString() for _ in range(length)]
    