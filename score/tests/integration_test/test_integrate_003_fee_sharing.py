from iconsdk.wallet.wallet import KeyWallet
from .test_integrate_omm_utils import OmmUtils
from ..actions.fee_sharing_1_usds_user_whitelisted import ACTIONS as FEE_SHARING_CASE1
from ..actions.fee_sharing_2_usds_user_not_whitelisted import ACTIONS as FEE_SHARING_CASE2
from ..actions.fee_sharing_3_usds_check_free_limit import ACTIONS as FEE_SHARING_CASE3
from ..actions.fee_sharing_4_multiple_users import ACTIONS as FEE_SHARING_CASE4
from ..actions.fee_sharing_5_icx_user_whitelisted import ACTIONS as FEE_SHARING_CASE5
from ..actions.fee_sharing_6_icx_user_not_whitelisted import ACTIONS as FEE_SHARING_CASE6
from ..actions.fee_sharing_7_borrow_all_deposited_usds import ACTIONS as FEE_SHARING_CASE7
from ..actions.steps import Steps

EXA = 10 ** 18
halfEXA = EXA // 2


class OMMFeeSharingCases(OmmUtils):
    def setUp(self):
        super().setUp()

    def test_01_bridge_whitelisted_wallets(self):
        self._execute(FEE_SHARING_CASE1)

    def test_02_bridge_depositors_not_whitelisted(self):
        self._execute(FEE_SHARING_CASE2)

    def test_03_check_free_tx_limit(self):
        self._execute(FEE_SHARING_CASE3)

    def test_04_check_free_tx_limit_multiple_users(self):
        self._execute(FEE_SHARING_CASE4)

    def test_05_bridge_deposited_icx_cases(self):
        self._execute(FEE_SHARING_CASE5)

    def test_06_bridge_not_deposited_icx_cases(self):
        self._execute(FEE_SHARING_CASE6)

    def test_07_user_withdraws_all_usds_cases(self):
        self._execute(FEE_SHARING_CASE7)

    def initialize_user(self, name: str, share_fee: bool = False):
        user = KeyWallet.create()
        self.send_icx(self.deployer_wallet, user.get_address(), 10 * EXA)
        if share_fee:
            tx = self._mintUSDS(self.deployer_wallet, user.get_address())

            self.assertEqual(tx['status'], 1)
            balance = self.call_tx(self.contracts['usds'], "balanceOf", {'_owner': user.get_address()})
            print(f"balance :: {balance}")
            tx = self._depositUSDS(user, 100 * EXA)
            self.assertEqual(tx['status'], 1)
        else:
            tx = self._transferUSDS(self.deployer_wallet, user.get_address(), 1000 * EXA)
            self.assertEqual(tx['status'], 1)
        self.users[name] = user

    def initialize_users(self, share_fee: int, n_users: int = 1):
        self.users = {
            "admin": self.deployer_wallet
        }
        share = False
        if share_fee == 1:
            share = True
        self.initialize_user("user1", share)
        if n_users == 2:
            self.initialize_user("user2")

    def _check_tx_result(self, tx_result, case):
        if (tx_result['status'] == 0):
            print("SCORE MESSAGE: ", tx_result['failure']['message'])
            if case.get('revertMessage') != None:
                print("EXPECTED MESSAGE: ", case['revertMessage'])

        self.assertEqual(tx_result['status'], case['expectedResult'])

    def _set_user_balances(self, key):
        self.balance[key][self.user]["icx"] = self.get_balance(self._user.get_address())

    def _after_tx(self, tx_res, case):
        if tx_res.get("status") == 1:
            self._set_user_balances("after")
            if case.get("remarks"):
                print(case.get("remarks"))
            if case.get("feeShared") == 1:
                self._test_fee_sharing()
            else:
                self.assertGreater(
                    self.balance["before"]["user1"]["icx"],
                    self.balance["after"]["user1"]["icx"]
                )
                print("User paid transaction fee")

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

        self.initialize_users(task.get("enableShare"), task.get("nUsers"))

        for case in task["transaction"]:
            _step = case.get("_step")
            self.user = case.get("user")  # name
            self._user = self.users.get(self.user)  # wallet
            _user = self.users.get(self.user)
            self.amount = case.get("amount")
            amount = case.get("amount")
            print(f"#################################{_step} by {self.user}####################################")

            if _step == Steps.DEPOSIT_USDS:
                self._set_user_balances("before")

                tx_res = self._depositUSDS(_user, amount)
                self._check_tx_result(tx_res, case)
                self._after_tx(tx_res, case)


            elif _step == Steps.BORROW_USDS:
                self._set_user_balances("before")

                tx_res = self._borrowUSDS(_user, amount)
                self._check_tx_result(tx_res, case)
                self._after_tx(tx_res, case)

            elif _step == Steps.REDEEM_USDS:
                self._set_user_balances("before")

                tx_res = self._redeemUSDS(_user, amount)
                self._check_tx_result(tx_res, case)

                self._after_tx(tx_res, case)

            elif _step == Steps.REPAY_USDS:
                self._set_user_balances("before")

                tx_res = self._repayUSDS(_user, amount)
                self._check_tx_result(tx_res, case)

                self._after_tx(tx_res, case)

            elif _step == Steps.DEPOSIT_ICX:
                self._set_user_balances("before")

                tx_res = self._depositICX(_user, amount)
                self._check_tx_result(tx_res, case)
                self._set_user_balances("after")

                icx_amt_before = self.balance["before"][self.user]["icx"]
                icx_amt_after = self.balance["after"][self.user]["icx"]

                if case.get("feeShared") == 1:
                    self.assertEqual(icx_amt_after, icx_amt_before - amount)
                    print("100% FEE SHARED BY CONTRACT")
                else:
                    self.assertGreater(icx_amt_before, icx_amt_after + amount)
                    print("User paid transaction fee")

            elif _step == Steps.BORROW_ICX:
                self._set_user_balances("before")

                tx_res = self._borrowICX(_user, amount)
                self._check_tx_result(tx_res, case)
                self._set_user_balances("after")
                self._after_tx(tx_res, case)

            elif _step == Steps.REDEEM_ICX:
                self._set_user_balances("before")

                tx_res = self._redeemICX(_user, amount)
                self._check_tx_result(tx_res, case)
                self._set_user_balances("after")
                self._after_tx(tx_res, case)

            elif _step == Steps.REPAY_ICX:
                self._set_user_balances("before")

                tx_res = self._repayICX(_user, amount)
                self._check_tx_result(tx_res, case)
                self._set_user_balances("after")
                self._after_tx(tx_res, case)

    def _test_fee_sharing(self):
        icx_amt_before = self.balance["before"][self.user]["icx"]
        icx_amt_after = self.balance["after"][self.user]["icx"]

        self.assertEqual(icx_amt_after, icx_amt_before)
        print("100% FEE SHARED BY CONTRACT")
