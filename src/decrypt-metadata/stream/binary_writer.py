import struct
import array


class BinaryWriter:
    def __init__(self, is_little_endian: bool):

        if is_little_endian:
            self.endian = "<"
        else:
            self.endian = ">"

        self.offset = 0
        self.data = bytearray()

    def write(self, format_string, *data):
        packed_data = struct.pack(self.endian + format_string, *data)
        self.data.extend(packed_data)
        self.offset += struct.calcsize(format_string)

    def writeBool(self, data):
        self.write("?", data)

    def writeInt8(self, data):
        self.write("b", data)

    def writeUInt8(self, data):
        self.write("B", data)

    def writeInt16(self, data):
        self.write("h", data)

    def writeUInt16(self, data):
        self.write("H", data)

    def writeInt32(self, data):
        self.write("i", data)

    def writeUInt32(self, data):
        self.write("I", data)

    def writeInt64(self, data):
        self.write("q", data)

    def writeUInt64(self, data):
        self.write("Q", data)

    def writeHalf(self, data):
        self.write("e", data)

    def writeFloat(self, data):
        self.write("f", data)

    def writeDouble(self, data):
        self.write("d", data)

    def writeBoolArray(self, data):
        self.write("?", *data)

    def writeInt8Array(self, data):
        self.write("b" * len(data), *data)

    def writeUInt8Array(self, data):
        self.write("B" * len(data), *data)
