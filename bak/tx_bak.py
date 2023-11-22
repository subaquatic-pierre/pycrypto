import hashlib
from io import BytesIO
from typing import Self, List
import pprint
import time
import requests
from dotenv import load_dotenv
import os

from utils import le_to_int, read_varint, encode_varint, int_to_le, decode_varint
from script import Script


load_dotenv()

API_KEY = os.environ.get("CRYPTO_API_KEY")

import json


# Length of entire transaction input byte array
TX_IN_BYTE_LEN = 32


class Input:
    def __init__(
        self,
        prev_tx: bytes,
        prev_index: int,
        script_sig: Script | None = None,
        sequence: int | None = 0xFFFFFFFF,
    ):
        self.prev_tx = prev_tx
        self.prev_index = prev_index

        if script_sig is None:
            self.script_sig = Script()
        else:
            self.script_sig = script_sig

        self.sequence = sequence

    def __repr__(self):
        return pprint.pformat(
            {"prev_tx": self.prev_tx.hex(), "prev_index": self.prev_index}, 4
        )

    def serialize(self) -> bytes:
        """Returns the byte serialization of the transaction input"""
        result = self.prev_tx[::-1]
        result += int_to_le(self.prev_index, 4)
        result += self.script_sig.serialize()
        result += int_to_le(self.sequence, 4)
        return result

    @classmethod
    def parse(cls, stream: BytesIO) -> Self:
        prev_tx = bytes([item for item in reversed(stream.read(32))])

        prev_index = le_to_int(stream.read(4))

        script_sig = Script.parse(stream)

        sequence = le_to_int(stream.read(4))

        return cls(prev_tx, prev_index, script_sig, sequence)

    @classmethod
    def from_hex(cls, stream: BytesIO) -> object:
        value = stream.read(8)
        pub_script_size = read_varint(stream)
        pk_script = stream.read(pub_script_size)

        return {
            "value": value,
            "pub_script_size": pub_script_size,
            "pk_script": pk_script,
        }


class Output:
    def __init__(self, amount: int, script_pubkey: bytes):
        self.amount = amount
        self.script_pubkey = script_pubkey

    def __repr__(self):
        return pprint.pformat(
            {"amount": self.amount, "script_pubkey": self.script_pubkey}, 4
        )

    def serialize(self) -> bytes:
        """Returns the byte serialization of the transaction output"""
        result = int_to_le(self.amount, 8)
        result += encode_varint(len(self.script_pubkey))
        result += self.script_pubkey
        return result

    @classmethod
    def parse(cls, stream: BytesIO) -> Self:
        amount = le_to_int(stream.read(8))

        # Get length of script pubkey, ignore first 8 bytes
        script_pubkey_len = read_varint(stream)

        # get rest of bytes used to script_pubkey
        script_pubkey = stream.read(script_pubkey_len)

        return cls(amount, script_pubkey)

    @classmethod
    def from_hex(cls, stream: BytesIO) -> object:
        value = stream.read(8)
        pub_script_size = read_varint(stream)
        pk_script = stream.read(pub_script_size)

        return {
            "value": value,
            "pub_script_size": pub_script_size,
            "pk_script": pk_script,
        }


class Transaction:
    def __init__(
        self,
        version: int,
        tx_ins: List[Input],
        tx_outs: List[Output],
        locktime: int,
        testnet=False,
    ):
        self.version = version
        self.tx_ins = tx_ins
        self.tx_outs = tx_outs
        self.locktime = locktime
        self.testnet = testnet

    def __repr__(self):
        return pprint.pformat(
            {
                "tx": self.id(),
                "version": self.version,
                "tx_ins": self.tx_ins,
                "tx_outs": self.tx_outs,
                "locktime": self.locktime,
            },
            4,
        )

    def id(self) -> str:
        """Human-readable hexadecimal of the transaction hash"""
        return self.hash().hex()

    def hash(self) -> bytes:
        """Binary hash of the legacy serialization"""
        return hashlib.sha256(self.serialize()).digest()[::-1]

    def serialize(self) -> bytes:
        result = int_to_le(self.version, 4)

        result += encode_varint(len(self.tx_ins))

        for tx_in in self.tx_ins:
            result += tx_in.serialize()

        result += encode_varint(len(self.tx_outs))

        for tx_out in self.tx_outs:
            result += tx_out.serialize()

        result += int_to_le(self.locktime, 4)
        return result

    @classmethod
    def parse(cls, stream: BytesIO) -> Self:
        serialized_version = stream.read(4)
        version = le_to_int(serialized_version)

        # get number of txs in stream
        # Remove first 4 bytes from stream as is version number
        num_tx_in = read_varint(stream)
        # get len of bytes used in varint for number of txs
        # num_tx_in_len = len(encode_varint(num_tx_in))

        # get initial byte offset to start reading from the stream
        # first 4 bytes are version
        # next bytes are varint number of txins
        # cur_byte_offset = 4 + num_tx_in_len

        # get all Input bytes
        # all_tx_in_bytes = stream.read(
        #     cur_byte_offset + (num_tx_in_len * TX_IN_BYTE_LEN)
        # )

        # Create empty array for tx ins
        tx_ins: List[Input] = []

        for _ in range(0, num_tx_in):
            # get raw bytes of current tx_in
            # tx_in_bytes = all_tx_in_bytes[cur_byte_offset:TX_IN_BYTE_LEN]

            # print(stream.read())

            # parse bytes to Input
            tx_in = Input.parse(stream)

            # push Input to array
            tx_ins.append(tx_in)

            # increment byte offset after each txin is read
            # cur_byte_offset += TX_IN_BYTE_LEN

        # get number of tx outs stream
        num_tx_out = read_varint(stream)
        # get len of bytes used in varint for number of txs
        # num_tx_out_len = len(encode_varint(num_tx_out))

        # increment cur_byte_offset by number bytes used in num_tx_out
        # cur_byte_offset += num_tx_out_len

        # get rest  bytes for TxOuts
        # all_bytes = stream.read()

        # Create empty array for tx outs
        tx_outs: List[Input] = []
        for _ in range(0, num_tx_out):
            # Get length of script pubkey, plus 8 bytes used for amount
            # script_pubkey_len = read_varint(BytesIO(all_bytes[(cur_byte_offset + 8) :]))

            # get number of bytes used as varint for length of script
            # script_pubkey_len_num_bytes = len(encode_varint(script_pubkey_len))

            # 8 bytes for amount + script length varint size + script length
            # tx_out_byte_len = 8 + script_pubkey_len_num_bytes + script_pubkey_len

            # Raw bytes for current tx out
            # tx_out_bytes = all_bytes[cur_byte_offset:tx_out_byte_len]

            # parsed Output
            tx_out = Output.parse(stream)

            # Append parsed Output to list
            tx_outs.append(tx_out)
            # increment cur_byte_offset to next tx_out
            # cur_byte_offset += tx_out_byte_len

        locktime = le_to_int(stream.read(4))

        # Return new class instance
        return cls(version, tx_ins, tx_outs, locktime)

    @classmethod
    def from_hex(cls, raw_hex: bytes) -> object:
        _hash = None
        _txid = None
        inputs = None
        outputs = None
        _version = None
        _locktime = None
        _size = None
        n_inputs = 0
        n_outputs = 0
        is_segwit = False

        offset = 4

        # adds basic support for segwit transactions
        #   - https://bitcoincore.org/en/segwit_wallet_dev/
        #   - https://en.bitcoin.it/wiki/Protocol_documentation#BlockTransactions
        if b"\x00\x01" == raw_hex[offset : offset + 2]:
            is_segwit = True
            offset += 2

        n_inputs, varint_size = decode_varint(raw_hex[offset:])
        offset += varint_size

        inputs = []
        for i in range(n_inputs):
            input = Input.from_hex(raw_hex[offset:])
            offset += input.size
            inputs.append(input)

        n_outputs, varint_size = decode_varint(raw_hex[offset:])
        offset += varint_size

        outputs = []
        for i in range(n_outputs):
            output = Output.from_hex(raw_hex[offset:])
            offset += output.size
            outputs.append(output)

        if is_segwit:
            _offset_before_tx_witnesses = offset
            for inp in inputs:
                tx_witnesses_n, varint_size = decode_varint(raw_hex[offset:])
                offset += varint_size
                for j in range(tx_witnesses_n):
                    component_length, varint_size = decode_varint(raw_hex[offset:])
                    offset += varint_size
                    witness = raw_hex[offset : offset + component_length]
                    inp.add_witness(witness)
                    offset += component_length

        _size = offset + 4
        hex = raw_hex[:_size]

        if _size != len(hex):
            raise Exception("Incomplete transaction!")


class TxFetcher:
    cache = {}

    @classmethod
    def get_url(cls, tx_id: str):
        return f"https://rest.cryptoapis.io/blockchain-data/bitcoin/testnet/transactions/{tx_id}"

    @classmethod
    def fetch(cls, tx_id, testnet=True, fresh=False):
        if fresh or (tx_id not in cls.cache):
            remote_api_caller = RemoteApiCaller()
            response = remote_api_caller.tx(tx_id)

            try:
                raw = bytes.fromhex(response.text.strip())
            except ValueError:
                raise ValueError("unexpected response: {}".format(response.text))
            if raw[4] == 0:
                raw = raw[:4] + raw[6:]
                tx = Transaction.parse(BytesIO(raw), testnet=testnet)
                tx.locktime = le_to_int(raw[-4:])
            else:
                tx = Transaction.parse(BytesIO(raw), testnet=testnet)
                if tx.id() != tx_id:
                    raise ValueError("not the same id: {} vs {}".format(tx.id(), tx_id))
            cls.cache[tx_id] = tx

        cls.cache[tx_id].testnet = testnet
        return cls.cache[tx_id]


class RemoteApiCaller:
    def __init__(self) -> None:
        self.api_key = API_KEY
        self.remote_host = "https://blockstream.info/testnet/api/"

    def tx(self, tx_id):
        url = f"{self.remote_host}/tx/{tx_id}"
        res = self._make_request(url)
        return res

    def tx_hex(self, tx_id):
        url = f"{self.remote_host}/tx/{tx_id}/hex"
        res = self._make_request(url, True)
        return res

    def list_block_txs(self, block_hash: str):
        url = f"{self.remote_host}/block/{block_hash}/txids"
        res = self._make_request(url)
        return res

    def list_blocks(self):
        url = f"{self.remote_host}/blocks"
        res = self._make_request(url)
        return res

    def block(self, block_hash):
        url = f"{self.remote_host}/block/{block_hash}"
        res = self._make_request(url)
        return res

    def _make_request(self, url, hex=False):
        try:
            response = requests.get(url, headers=self._get_headers())

            if hex:
                return response.text

            json = response.json()
            return json

        except ValueError:
            raise ValueError("unexpected response: {}".format(response.text.strip()))

    def _get_headers(self):
        return {"Content-Type": "application/json", "X-API-Key": self.api_key}
