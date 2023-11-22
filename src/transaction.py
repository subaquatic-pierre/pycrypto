import hashlib
from io import BytesIO
from typing import Self, List
import pprint
import time
import requests
from dotenv import load_dotenv
import os

from utils import (
    le_to_int,
    read_varint,
    encode_varint,
    int_to_le,
    decode_varint,
    double_sha256,
    format_hash,
    decode_uint32,
)

from script import Script
from output import Output
from math import ceil
from input import Input


load_dotenv()

API_KEY = os.environ.get("CRYPTO_API_KEY")

import json


# Length of entire transaction input byte array
TX_IN_BYTE_LEN = 32


class Transaction:
    """Represents a bitcoin transaction"""

    def __init__(self, raw_hex: bytes):
        self._hash = None
        self._txid = None
        self.inputs = None
        self.outputs = None
        self._version = None
        self._locktime = None
        self._size = None
        self.n_inputs = 0
        self.n_outputs = 0
        self.is_segwit = False

        offset = 4

        # adds basic support for segwit transactions
        #   - https://bitcoincore.org/en/segwit_wallet_dev/
        #   - https://en.bitcoin.it/wiki/Protocol_documentation#BlockTransactions
        if b"\x00\x01" == raw_hex[offset : offset + 2]:
            self.is_segwit = True
            offset += 2

        self.n_inputs, varint_size = decode_varint(raw_hex[offset:])
        offset += varint_size

        self.inputs = []
        for i in range(self.n_inputs):
            input = Input.from_hex(raw_hex[offset:])
            offset += input.size
            self.inputs.append(input)

        self.n_outputs, varint_size = decode_varint(raw_hex[offset:])
        offset += varint_size

        self.outputs = []
        for i in range(self.n_outputs):
            output = Output.from_hex(raw_hex[offset:])
            offset += output.size
            self.outputs.append(output)

        if self.is_segwit:
            self._offset_before_tx_witnesses = offset
            for inp in self.inputs:
                tx_witnesses_n, varint_size = decode_varint(raw_hex[offset:])
                offset += varint_size
                for j in range(tx_witnesses_n):
                    component_length, varint_size = decode_varint(raw_hex[offset:])
                    offset += varint_size
                    witness = raw_hex[offset : offset + component_length]
                    inp.add_witness(witness)
                    offset += component_length

        self._size = offset + 4
        self.hex = raw_hex[: self._size]

        if self._size != len(self.hex):
            raise Exception("Incomplete transaction!")

    def __repr__(self):
        return f"Transaction({self.hash})"

    @property
    def version(self):
        """Returns the transaction's version number"""
        if self._version is None:
            self._version = decode_uint32(self.hex[:4])
        return self._version

    @property
    def locktime(self):
        """Returns the transaction's locktime as an int"""
        if self._locktime is None:
            self._locktime = decode_uint32(self.hex[-4:])
        return self._locktime

    @property
    def hash(self):
        """Returns the transaction's id. Equivalent to the hash for non SegWit transactions,
        it differs from it for SegWit ones."""
        if self._hash is None:
            self._hash = format_hash(double_sha256(self.hex))

        return self._hash

    @property
    def size(self):
        """Returns the transactions size in bytes including the size of the
        witness data if there is any."""
        return self._size

    @property
    def vsize(self):
        """Returns the transaction size in virtual bytes."""
        if not self.is_segwit:
            return self._size
        else:
            # the witness is the last element in a transaction before the
            # 4 byte locktime and self._offset_before_tx_witnesses is the
            # position where the witness starts
            witness_size = self._size - self._offset_before_tx_witnesses - 4

            # size of the transaction without the segwit marker (2 bytes) and
            # the witness
            stripped_size = self._size - (2 + witness_size)
            weight = stripped_size * 3 + self._size

            # vsize is weight / 4 rounded up
            return ceil(weight / 4)

    @property
    def txid(self):
        """Returns the transaction's id. Equivalent to the hash for non SegWit transactions,
        it differs from it for SegWit ones."""
        if self._txid is None:
            # segwit transactions have two transaction ids/hashes, txid and wtxid
            # txid is a hash of all of the legacy transaction fields only
            if self.is_segwit:
                txid_data = (
                    self.hex[:4]
                    + self.hex[6 : self._offset_before_tx_witnesses]
                    + self.hex[-4:]
                )
            else:
                txid_data = self.hex
            self._txid = format_hash(double_sha256(txid_data))

        return self._txid

    def is_coinbase(self):
        """Returns whether the transaction is a coinbase transaction"""
        for input in self.inputs:
            if input.transaction_hash == "0" * 64:
                return True
        return False

    def uses_replace_by_fee(self):
        """Returns whether the transaction opted-in for RBF"""
        # Coinbase transactions may have a sequence number that signals RBF
        # but they cannot use it as it's only enforced for non-coinbase txs
        if self.is_coinbase():
            return False

        # A transactions opts-in for RBF when having an input
        # with a sequence number < MAX_INT - 1
        for input in self.inputs:
            if input.sequence_number < 4294967294:
                return True
        return False

    def to_hex(self) -> bytes:
        result = int_to_le(self.version, 4)

        result += encode_varint(len(self.tx_ins))

        for tx_in in self.tx_ins:
            result += tx_in.serialize()

        result += encode_varint(len(self.tx_outs))

        for tx_out in self.tx_outs:
            result += tx_out.serialize()

        result += int_to_le(self.locktime, 4)
        return result

    def to_json():
        return {}

    @classmethod
    def from_hex(cls, hex: bytes):
        return cls(hex)
