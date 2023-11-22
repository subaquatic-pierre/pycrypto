import math
import hashlib
import struct


def le_to_int(bytes: bytes) -> int:
    return int.from_bytes(bytes, "little")


def int_to_le(num: int, num_bytes: int) -> bytes:
    # number_of_bytes = int(math.ceil(num.bit_length() / 8))

    return num.to_bytes(num_bytes, "little")


def read_varint(stream) -> int:
    """read_varint reads a variable integer from a stream"""
    i = stream.read(1)[0]
    """Parses a compact uint and return the value as well as the number of
    bytes consumed
    >>> parse_cuint(bytes([0xfa]))
    (250, 1)
    >>> parse_cuint(bytes([0xfd, 0xd2, 0x04]))
    (1234, 3)
    >>> parse_cuint(bytes([0xfe, 0x15, 0xcd, 0x5b, 0x07]))
    (123456789, 5)
    >>> parse_cuint(bytes([0xff, 0x15, 0x5f, 0xd0, 0xac, 0x4b, 0x9b, 0xb6, 0x01]))
    (123456789123456789, 9)
    """
    if i < 0xFD:
        return i
    elif i == 0xFD:
        return int.from_bytes(stream.read(2), "little")
    elif i == 0xFE:
        return int.from_bytes(stream.read(4), "little")
    else:  # cuint[0] == 0xff:
        return int.from_bytes(stream.read(8), "little")


def encode_varint(i: int) -> bytes:
    """encodes an integer as a varint"""
    if i < 0xFD:
        return bytes([i])
    elif i < 0x10000:
        return b"\xfd" + int_to_le(i, 2)
    elif i < 0x100000000:
        return b"\xfe" + int_to_le(i, 4)
    elif i < 0x10000000000000000:
        return b"\xff" + int_to_le(i, 8)
    else:
        raise ValueError("integer too large: {}".format(i))


def decode_varint(data: bytes):
    assert len(data) > 0
    size = int(data[0])
    assert size <= 255

    if size < 253:
        return size, 1

    if size == 253:
        format_ = "<H"
    elif size == 254:
        format_ = "<I"
    elif size == 255:
        format_ = "<Q"
    else:
        # Should never be reached
        assert 0, "unknown format_ for size : %s" % size

    size = struct.calcsize(format_)
    return struct.unpack(format_, data[1 : size + 1])[0], size + 1


def format_hash(hash_: bytes):
    return hash_[::-1].hex()


def double_sha256(data: bytes):
    return hashlib.sha256(hashlib.sha256(data).digest()).digest()


def decode_uint32(data):
    assert len(data) == 4
    return struct.unpack("<I", data)[0]


def decode_uint64(data):
    assert len(data) == 8
    return struct.unpack("<Q", data)[0]


def btc_ripemd160(data):
    h1 = hashlib.sha256(data).digest()
    r160 = hashlib.new("ripemd160")
    r160.update(h1)
    return r160.digest()
