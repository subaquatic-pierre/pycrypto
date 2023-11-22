from typing import Self
from utils import read_varint, encode_varint


class Script:
    def __init__(self, bytes: bytes) -> None:
        self.bytes = bytes

    def serialize(self) -> bytes:
        result = encode_varint(len(self.bytes))
        result += self.bytes
        return result

    @classmethod
    def parse(cls, stream) -> Self:
        script_sig_len = read_varint(stream)

        # TODO: contstruct Script object
        script_sig = stream.read(script_sig_len)

        return cls(script_sig)
