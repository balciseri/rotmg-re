"""
Decrypt and unshuffle IL2CPP global-metadata.dat
"""

from pathlib import Path
import xxtea

from stream import BinaryReader, BinaryWriter

ENDIANNESS = "little"
IS_LITTLE_ENDIAN = ENDIANNESS == "little"

METADATA_SANITY = bytearray.fromhex("AF1BB1FA")
METADATA_VERSION = (29).to_bytes(4, byteorder=ENDIANNESS)  # 1D 00 00 00


def read_binary_file(file_path: Path) -> bytes:
    """Returns a binary file's data"""
    with open(file_path, "rb") as file:
        return file.read()


def write_binary_file(file_path: Path, value: bytes) -> bytes:
    """Write binary to a file on disk. Will not overwrite existing an existing file"""
    if file_path.exists():
        print(f"Error: file '{file_path}' already exists.")
        raise FileExistsError

    with open(file_path, "wb") as file:
        return file.write(value)


def xor(byte_arr: bytearray, key: bytearray) -> bytearray:
    """XOR's a bytearray with the given key"""
    result = bytearray()
    for i, byte in enumerate(byte_arr):
        result.append(byte ^ key[i % len(key)])
    return result


class DecryptMetadata:
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.data = read_binary_file(self.file_path)
        self.header: bytearray = None
        self.header_offset = -1
        self.header_size = -1

    def decrypt_header(self):
        # Header info
        reader = BinaryReader(self.data, IS_LITTLE_ENDIAN)
        random_string = reader.readStringC()
        self.header_offset = reader.readInt32()
        self.header_size = reader.readUInt32()

        print(f"First string: {random_string}")
        print(f"Header offset: {self.header_offset}")
        print(f"Header size: {self.header_size}")

        # Encrypted Header
        start = self.header_offset
        end = self.header_offset + self.header_size
        encrypted_header = self.data[start:end]

        # Decrypt the header
        key = self.xxtea_key()
        decrypted_header = xxtea.decrypt(encrypted_header, key, padding=False)

        # For some reason the length of the header is added to the end
        # Removing this for now, will be added back after unshuffling the header.
        decrypted_header = decrypted_header[:-4]

        self.header = decrypted_header
        print("Header successfully decrypted!")
        print(f"Header: {self.header.hex()}")

    def xxtea_key(self):
        """Returns the deciphered xxtea key"""
        encrypted_key = b"##%$vsw'lytyqlusxul##p\"lvxrsv\"y\"y'xu%tv\"qsy\"l%%#qlux'ul# wylys\"t 'v$us''A"
        xor_key = b"\x41"
        key = xor(encrypted_key, xor_key)
        return key[:16]

    def unshuffle_header(self):
        correct_header = BinaryWriter(IS_LITTLE_ENDIAN)
        header_copy = bytearray.fromhex(self.header.hex())

        # We know the header begins with two unique constants
        self.check_sanity()
        self.check_version()
        header_copy = header_copy.replace(METADATA_SANITY, b"")
        header_copy = header_copy.replace(METADATA_VERSION, b"")
        correct_header.data += METADATA_SANITY
        correct_header.data += METADATA_VERSION

        # The rest of the data in the header is the offsets/sizes of segments in the metadata
        # To unshuffle the header, we leverage the fact that given an offset + it's size is equal to the next offset
        # And the offsets are in ascending order (i.e. in the order they appear in Il2CppGlobalMetadataHeader)
        remaining_ints = []
        reader = BinaryReader(header_copy, IS_LITTLE_ENDIAN)
        while reader.offset < len(reader.stream):
            remaining_ints.append(reader.readInt32())

        remaining_ints = sorted(remaining_ints)

        # Need a valid offset to start with. We're asssuming the first Int32 (that isn't zero) is a valid offset.
        # However, it might be possible that this fails, as a size could be smaller than the the first offset
        offset = [x for x in remaining_ints if x != 0][0]
        remaining_ints.remove(offset)

        pairs: list[tuple] = []
        while True:
            size, next_offset = self._find_offset_size(offset, remaining_ints)
            if size is None:
                print(f"Could not find size for offset {offset}")
                continue

            pair = (offset, size)
            pairs.append(pair)
            print(
                f"Found offset={pair[0]}, size={pair[1]}. Next offset: {next_offset}")

            # Found all offsets, break
            if len(remaining_ints) == 1:
                break

            remaining_ints.remove(size)
            remaining_ints.remove(next_offset)
            offset = next_offset

        # Write the offsets and sizes to the header
        for offset, size in pairs:
            correct_header.writeUInt32(offset)
            correct_header.writeInt32(size)

        print(f"Successfully unshuffled {len(pairs)} offsets!")
        self.header = correct_header.data

    def _find_offset_size(self, offset, ints):
        # The last offset won't have a next_offset
        if len(ints) == 1:
            return (ints[0], offset)

        # Try all the remaining integers
        for size in ints:
            new_offset = offset + size

            # if offset + size is equal to an integer that exists, then we found the correct size and next_offset
            if new_offset in ints:
                return (size, new_offset)

            # Sometimes the next offset is one Int32 (4 bytes), unsure why
            if new_offset + 4 in ints:
                return (size, new_offset + 4)

        return (None, None)

    def check_sanity(self):
        """Check if the header contains the sanity bytes"""
        if not METADATA_SANITY in self.header:
            print(
                f"Unable to find sanity bytes '{METADATA_SANITY.hex()}' in metadata header!")
            raise RuntimeError

        print(f"Found sanity bytes: {METADATA_SANITY.hex()}")

    def check_version(self):
        """Check if the header contains the supported metadata version"""
        if not METADATA_VERSION in self.header:
            print(
                f"Unable to find version bytes'{METADATA_VERSION.hex()}' in metadata header!")
            raise RuntimeError

        print(f"Found version bytes: {METADATA_VERSION.hex()}")

    def output(self, filename):
        """Write the final metadata to disk. Will not overwrite an existing file"""
        output_filepath: Path = self.file_path.parent / filename

        output = BinaryWriter(IS_LITTLE_ENDIAN)
        output.data += self.header
        output.writeInt32(len(self.header))
        output.data += self.data[self.header_size:]
        write_binary_file(output_filepath, output.data)

        relative_path = output_filepath.relative_to(Path.cwd())
        print(f"Output: {relative_path}")


def main():
    metadata_in = Path.cwd() / "global-metadata.dat"
    metadata_out = Path.cwd() / "global-metadata-fixed.dat"

    metadata = DecryptMetadata(metadata_in)
    metadata.decrypt_header()
    metadata.unshuffle_header()
    metadata.output(metadata_out)


main()
