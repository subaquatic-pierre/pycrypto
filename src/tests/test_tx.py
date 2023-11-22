from unittest import TestCase
from io import BytesIO
from transaction import Transaction, Input, Output
from tx_fetcher import TxFetcher, RemoteApiCaller
import pprint


def print(*args, **kwargs):
    return pprint.pprint(*args, **kwargs)


coin_base_tx_hash = "cc811b3e82cd17a168314c26462aefa30b7758a4746e83e58a4acd6cc0a05f10"
block_hash = "00000000bae9afe6af6e1d55d658b3f1236f7e4cfb7be0d0a7929f5afff83518"
tx_hash = "6752b3327aacb5ead3ab0c9418647cd746439c73411c527502f042cefe1fb444"

raw_hex = "0200000000010567c888456b61170d52a77f74974c92a6075aba4a151b892f119c9916ba9f33c80100000000feffffff48153e6dc07cc74f4bffcadb422c782ff73f9d9e55291c4ae7e5f720889af87a0000000000feffffff8d1c2a870b54bf561853a16e6531c4b71e2b9f47d9733ab02db06ad62b5f23eb0000000000feffffff9d45e542db7debc57e05861dfe1a166f78c6c8530d81aaaf3dbca66764d4f0a50000000000feffffff87cd1224509703c8bbdd0a533b6bde75253d820b32d7ca3d27707100c47f9c470100000000feffffff02bc3610000000000016001461940c8869fb34571086a8988c1a972daed1af83c82c0100000000001600145d576a81f460e7a1ed254fe9bfff075ab3bc45650247304402207fcd9d1e7e4faea1a617e07247365da6578cbb2ef620b230c0342569aaa26b330220133e24aa39bd73803a2255b211c33f08540dae76e04b3cec2a2672602b3fc509012102549fa9f712caffdf63da7d077e6a26dc3d01ca275312e9f64d1d9accf949d2bc02473044022065e723455564308b50ea91d0d6fe0593fbc5f755f97c42ecedb7981b8a50709802200c7b814941d576abfc71d674f6e53b3fa58006d9dcbfeaf49c510a7d55e912ee012102549fa9f712caffdf63da7d077e6a26dc3d01ca275312e9f64d1d9accf949d2bc0247304402205f6ad17b42bf6ca4f8a3dd08160d8290f422c8f1b40f2983af612c1a2cad344e0220301439ee0df745b4ad1d752ca58dac561ab1248fb7805d66d0f736e6ef663e67012102549fa9f712caffdf63da7d077e6a26dc3d01ca275312e9f64d1d9accf949d2bc02473044022021ec3be2240ba288981cd3eba70d4ef1dd0d93071d20b067924427b58875be0d022034726ac77af04b07dda662d10c27b6478e704741dc5d09718573d76c64c6ef95012102549fa9f712caffdf63da7d077e6a26dc3d01ca275312e9f64d1d9accf949d2bc02473044022053ef8fa434c9c5ced7cf4c230ce07d3b1c4c0fbf6f61810c9c903eccdf8358e902200d9f6126ed6d4b2073ede8d8623007da7862bd1afc069043938cb422e2a34b68012102549fa9f712caffdf63da7d077e6a26dc3d01ca275312e9f64d1d9accf949d2bc791b2500"


class TestTx(TestCase):
    def test_parse_tx(self):
        raw_tx = bytes.fromhex(raw_hex)
        tx = Transaction.from_hex(raw_tx)

        # print(tx)

        # print(tx)
        self.assertEqual(tx.version, 2)


# class TestTxFetcher(TestCase):
#     def test_fetch_tx(self):
#         pass


class TestRemoteAPICaller(TestCase):
    def setUp(self) -> None:
        self.caller = RemoteApiCaller()
        return super().setUp()

    def test_list_blocks(self):
        res = self.caller.list_blocks()

        # print(res)

        pass

        # self.assertGreater(len(res["data"]["items"]), 0)

    def test_tx(self):
        blocks = self.caller.list_blocks()

        block_hash = blocks[0].get("id")
        res = self.caller.list_block_txs(block_hash)

        coinbase_tx_hash = res[0]

        tx_hex_res = self.caller.tx_hex(coinbase_tx_hash)
        coinbase_tx_hash = bytes.fromhex(tx_hex_res)

        coinbase_tx = Transaction.from_hex(coinbase_tx_hash)

        tx_hash = res[1]

        tx_hash = self.caller.tx_hex(tx_hash)

        tx_bytes = bytes.fromhex(tx_hash)

        tx = Transaction.from_hex(tx_bytes)

        print(tx.to_json())
