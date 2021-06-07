import os
from iconsdk.builder.transaction_builder import CallTransactionBuilder, TransactionBuilder
from iconsdk.exception import JSONRPCException
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from tbears.libs.icon_integrate_test import SCORE_INSTALL_ADDRESS, IconIntegrateTestBase
from iconsdk.builder.call_builder import CallBuilder

T_BEARS_URL = os.environ.get("T_BEARS_URL") or "http://127.0.0.1:9000"

print(f"T-Bears URL {T_BEARS_URL}")


class RegisterPReps(IconIntegrateTestBase):

    def setUp(self):
        super().setUp(network_only=True)
        self.icon_service = IconService(HTTPProvider(T_BEARS_URL, 3))
        self.nid = 3
        self.tx_result_wait = 5
        self._register_preps()

    def _register_preps(self):
        has_enough_preps = False
        self.count = 0
        preps_count = 0
        try:
            params = {"startRanking": 1, "endRanking": 100}
            params = {} if params is None else params
            call = CallBuilder(
                to=SCORE_INSTALL_ADDRESS,
                method="getPReps",
                params=params
            ).build()
            tx_result = self.process_call(call, self.icon_service)
            if "preps" in tx_result:
                preps_count = len(tx_result['preps'])
                has_enough_preps = preps_count >= 100
            else:
                print("not enough P-Reps")
        except JSONRPCException:
            has_enough_preps = False
        if has_enough_preps is False:
            print("registering P-Reps...")
            self._register_100_preps(20, 50)
            self._register_100_preps(50, 80)
            self._register_100_preps(80, 110)
            self._register_100_preps(110, 140)
            print("P-Reps registered.")
        else:
            print(f"t-bears has {preps_count} P-Reps")

    def test_init(self):
        self.assertEqual(1, 1, "P-Reps configuration successful")

    def _register_100_preps(self, start, end):
        txs = []
        send_icx_txs = []
        print(f"registering {end - start} P-Reps")
        for i in range(start, end):
            node_address = "hx9eec61296a7010c867ce24c20e69588e283212" + hex(i)[2:]
            params = {
                "name": f'Test P-rep{str(i)}',
                "country": "KOR",
                "city": "Unknown",
                "email": f'node{node_address}@example.com',
                "website": f'https://node{node_address}.example.com',
                "details": f'https://node{node_address}.example.com/details',
                "p2pEndpoint": f'node{node_address}.example.com:7100',
                "nodeAddress": node_address
            }
            wallet = self._wallet_array[i]
            send_icx_txs.append(self.build_send_icx(self._test1, wallet.get_address(), 3000000000000000000000))
            txs.append(self.build_tx(wallet, SCORE_INSTALL_ADDRESS,
                                     2000000000000000000000, "registerPRep", params))
        self.process_transaction_bulk(send_icx_txs, self.icon_service, 10)
        self.process_transaction_bulk(txs, self.icon_service, 10)
        self.count += end - start
        print(f"{self.count} P-Reps registered")

    def build_tx(self, from_: KeyWallet, to: str, value: int = 0, method: str = None, params: dict = None) \
            -> SignedTransaction:
        params = {} if params is None else params
        tx = CallTransactionBuilder(
            from_=from_.get_address(),
            to=to,
            value=value,
            step_limit=3_000_000_000,
            nid=self.nid,
            nonce=5,
            method=method,
            params=params
        ).build()
        signed_transaction = SignedTransaction(tx, from_)
        return signed_transaction

    def build_send_icx(self, from_: KeyWallet, to: str, value: int,
                       step_limit: int = 1000000, nonce: int = 3) -> SignedTransaction:
        send_icx_transaction = TransactionBuilder(
            from_=from_.get_address(),
            to=to,
            value=value,
            step_limit=step_limit,
            nid=self.nid,
            nonce=nonce
        ).build()
        signed_icx_transaction = SignedTransaction(send_icx_transaction, from_)
        return signed_icx_transaction
