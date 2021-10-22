from iconsdk.wallet.wallet import KeyWallet
from .test_integrate_omm_utils import OmmUtils
from pprint import pprint
from ..actions.steps import Steps
from ..actions.token_transfers import ACTIONS as TOKEN_TRANSFER

EXA = 10 ** 18


class TokenTransfer(OmmUtils):
    """interation tests for OmmTokenTransfers"""

    def setUp(self):
        super().setUp()

    def test_01_transfer_tokens(self):
        self._execute(TOKEN_TRANSFER)

    def _initialize_user(self, name: str):
        user = KeyWallet.create()
        self.send_icx(self.deployer_wallet, user.get_address(), 10 * EXA)
        tx = self._transferUSDS(self.deployer_wallet,
                                user.get_address(), 1000 * EXA)
        self.assertEqual(tx['status'], 1)
        self.users[name] = user
        self._balances(user.get_address())

    def _balances(self, addr):
        a = self.call_tx(
            to=self.contracts['usds'], method="balanceOf", params={'_owner': addr})

    def initialize_users(self):
        self.users = {
            "admin": self.deployer_wallet
        }

        self._initialize_user("user1")
        self._initialize_user("user2")

    def _check_tx_result(self, tx_result, case):
        if (tx_result['status'] == 0):
            print("SCORE MESSAGE: ", tx_result['failure']['message'])
            if case.get('revertMessage') != None:
                print("EXPECTED MESSAGE: ", case['revertMessage'])

        self.assertEqual(tx_result['status'], case['expectedResult'])

    def _execute(self, task):
        print("\n", task.get("description"))
        self.balance = {
            "before": {
                "user1": {},
                "user2": {}
            },
            "after": {
                "user1": {},
                "user2": {}
            }
        }

        self.initialize_users()
        for case in task.get("transaction"):
            _step = case.get("_step")
            self.user = case.get("user")
            self._user = self.users.get(self.user)
            self._to = self.users.get(case.get("to"))
            self._amount = case.get("amount")
            _success = case.get("expectedResult")
            print(
                f"#################################{_step} by {self.user}####################################")

            if _step == Steps.DEPOSIT_USDS:
                tx_res = self._depositUSDS(self._user, self._amount)
                self._check_tx_result(tx_res, case)

            elif _step == Steps.BORROW_ICX:
                tx_res = self._borrowICX(self._user, self._amount)
                self._check_tx_result(tx_res, case)

            elif _step == Steps.TRANSFER_OUSDS:
                self._set_balance("before")
                tx_res = self._transferOUSDS(
                    self._user, self._to.get_address(), self._amount)
                self._check_tx_result(tx_res, case)
                if case.get('expectedResult') == 1:
                    self._set_balance("after")
                    self._check()

            elif _step == Steps.TRANSFER_DICX:
                tx_res = self._transferDICX(
                    self._user, self._to.get_address(), self._amount)
                self._check_tx_result(tx_res, case)

    def _check(self):
        user1_before = int(self.balance['before']['user1'], 0)/10**18
        user1_after = int(self.balance['after']['user1'], 0)/10**18
        user2_before = int(self.balance['before']['user2'], 0)/10**18
        user2_after = int(self.balance['after']['user2'], 0)/10**18
        _amount = self._amount/10**18

        self.assertAlmostEqual(user1_after + _amount, user1_before, 5)
        self.assertAlmostEqual(user2_after, user2_before + _amount, 5)

    def _set_balance(self, key):
        self.balance[key]['user1'] = self._balance_of(self._user.get_address())
        self.balance[key]['user2'] = self._balance_of(self._to.get_address())

    def _balance_of(self, addr):
        return self.call_tx(
            to=self.contracts['oUSDS'],
            method="principalBalanceOf",
            params={'_user': addr}
        )
