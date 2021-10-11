from time import sleep
from typing import Union, List

from checkscore.repeater import retry
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import TransactionBuilder, DeployTransactionBuilder, CallTransactionBuilder
from iconsdk.exception import JSONRPCException
from iconsdk.builder.transaction_builder import TransactionBuilder, DeployTransactionBuilder, CallTransactionBuilder, \
    DepositTransactionBuilder
from iconsdk.icon_service import IconService
from iconsdk.libs.in_memory_zip import gen_deploy_data_content
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.wallet.wallet import KeyWallet
from iconservice.base.address import Address
from tbears.config.tbears_config import tbears_server_config, TConfigKey as TbConf
from tbears.libs.icon_integrate_test import Account
from tbears.libs.icon_integrate_test import IconIntegrateTestBase, SCORE_INSTALL_ADDRESS


def get_key(my_dict: dict, value: Union[str, int]):
    return list(my_dict.keys())[list(my_dict.values()).index(value)]


class TestUtils(IconIntegrateTestBase):

    def setUp(self,
              genesis_accounts: List[Account] = None,
              block_confirm_interval: int = tbears_server_config[TbConf.BLOCK_CONFIRM_INTERVAL],
              network_only: bool = False,
              network_delay_ms: int = tbears_server_config[TbConf.NETWORK_DELAY_MS],
              icon_service: IconService = None,
              nid: int = 3,
              tx_result_wait: int = 3):
        super().setUp(genesis_accounts, block_confirm_interval, network_only, network_delay_ms)
        self.icon_service = icon_service
        self.nid = nid
        self.tx_result_wait = tx_result_wait

    def deploy_tx(self,
                  from_: KeyWallet,
                  to: str = SCORE_INSTALL_ADDRESS,
                  value: int = 0,
                  content: str = None,
                  params: dict = None) -> dict:
        signed_transaction = self.build_deploy_tx(
            from_, to, value, content, params)
        tx_result = self.process_transaction(signed_transaction, network=self.icon_service,
                                             block_confirm_interval=self.tx_result_wait)

        self.assertTrue('status' in tx_result, tx_result)
        self.assertEqual(
            1, tx_result['status'], f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
        self.assertTrue('scoreAddress' in tx_result)

        return tx_result

    def build_deploy_tx(self,
                        from_: KeyWallet,
                        to: str = SCORE_INSTALL_ADDRESS,
                        value: int = 0,
                        content: str = None,
                        params: dict = None,
                        step_limit: int = 3_000_000_000,
                        nonce: int = 100) -> SignedTransaction:
        print(
            f"---------------------------Deploying contract: {content}---------------------------------------")
        print(content)
        params = {} if params is None else params
        transaction = DeployTransactionBuilder() \
            .from_(from_.get_address()) \
            .to(to) \
            .value(value) \
            .step_limit(step_limit) \
            .nid(self.nid) \
            .nonce(nonce) \
            .content_type("application/zip") \
            .content(gen_deploy_data_content(content)) \
            .params(params) \
            .build()

        signed_transaction = SignedTransaction(transaction, from_)
        return signed_transaction

    def send_icx(self, from_: KeyWallet, to: str, value: int):
        previous_to_balance = self.get_balance(to)
        previous_from_balance = self.get_balance(from_.get_address())

        signed_icx_transaction = self.build_send_icx(from_, to, value)
        tx_result = self.process_transaction(
            signed_icx_transaction, self.icon_service, self._block_confirm_interval)

        self.assertTrue('status' in tx_result, tx_result)
        self.assertEqual(
            1, tx_result['status'], f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
        fee = tx_result['stepPrice'] * tx_result['cumulativeStepUsed']
        self.assertEqual(previous_to_balance + value, self.get_balance(to))
        self.assertEqual(previous_from_balance - value - fee,
                         self.get_balance(from_.get_address()))

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

    def get_balance(self, address: str) -> int:
        if self.icon_service is not None:
            return self.icon_service.get_balance(address)
        params = {'address': Address.from_string(address)}
        response = self.icon_service_engine.query(
            method="icx_getBalance", params=params)
        return response

    def send_tx(self, from_: KeyWallet, to: Address, value: int = 0, method: str = None, params: dict = None) -> dict:
        # print(
        #     f"------------Calling {method}, with params={params} to {to} contract----------")
        signed_transaction = self.build_tx(from_, to, value, method, params)
        tx_result = self.process_transaction(
            signed_transaction, self.icon_service, self.tx_result_wait)

        self.assertTrue('status' in tx_result)
        print(tx_result['txHash'])
        # self.assertEqual(
        #     1, tx_result['status'], f"Failure: {tx_result['failure']}" if tx_result['status'] == 0 else "")
        return tx_result

    def build_tx(self, from_: KeyWallet, to: str, value: int = 0, method: str = None, params: dict = None) \
            -> SignedTransaction:
        params = {} if params is None else params
        tx = CallTransactionBuilder(
            from_=from_.get_address(),
            to=to,
            value=value,
            step_limit=300_000_000,
            nid=self.nid,
            nonce=5,
            method=method,
            params=params
        ).build()
        signed_transaction = SignedTransaction(tx, from_)
        return signed_transaction

    def deposit_tx(self, from_: KeyWallet, to: str, value: int = 5000000000000000000000) -> SignedTransaction:
        tx = DepositTransactionBuilder(
            from_=from_.get_address(),
            to=to,
            nid=3,
            value=value,
            step_limit=1000000000,
            nonce=100,
            action="add"
        ).build()
        signed_transaction = SignedTransaction(tx, from_)
        return signed_transaction

    def call_tx(self, to: str, method: str, params: dict = None):
        params = {} if params is None else params
        call = CallBuilder(
            to=to,
            method=method,
            params=params
        ).build()
        response = self.process_call(call, self.icon_service)
        # print(
        #     f"-----Reading method={method}, with params={params} on the {to} contract------\n")
        # print(f"-------------------The output is: : ")
        # pprint(response)
        return response


    def process_transaction(self, request: SignedTransaction,
                            network: IconService = None,
                            block_confirm_interval: int = -1) -> dict:
        if block_confirm_interval == -1:
            block_confirm_interval = self._block_confirm_interval

        tx_hash: str = network.send_transaction(request)
        sleep(block_confirm_interval + 0.1)
        # Get transaction result
        tx_result: dict = self.get_tx_result(tx_hash)

        return tx_result

    @retry(JSONRPCException, tries=10, delay=2, back_off=2)
    def get_tx_result(self, _tx_hash):
        try:
            print("_tx_hash", _tx_hash)
            tx_result = self.icon_service.get_transaction_result(_tx_hash)
            return tx_result
        except JSONRPCException as err:
            print(err)
            raise err
