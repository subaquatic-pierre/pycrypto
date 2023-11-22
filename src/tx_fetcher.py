from io import BytesIO
import requests
from dotenv import load_dotenv
import os

from utils import (
    le_to_int,
)

from transaction import Transaction


load_dotenv()

API_KEY = os.environ.get("CRYPTO_API_KEY")

import json


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
