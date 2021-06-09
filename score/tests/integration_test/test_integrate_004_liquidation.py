import json

from iconsdk.wallet.wallet import KeyWallet

from .test_integrate_omm_cases import OMMTestCases
from ..actions.liquidation1_single_collateral_single_borrow import ACTIONS as SINGLE_COLLATERAL_SINGLE_BORROW
from ..actions.liquidation2_multi_collateral_single_borrow import ACTIONS as MULTI_COLLATERAL_SINGLE_BORROW
from ..actions.liquidation3_single_collateral_single_borrow2 import ACTIONS as SINGLE_COLLATERAL_SINGLE_BORROW2
from ..actions.liquidation4_multi_collateral_single_borrow2 import ACTIONS as MULTI_COLLATERAL_SINGLE_BORROW2
from ..actions.liquidation5_single_collateral_multi_borrow import ACTIONS as SINGLE_COLLATERAL_MULTI_BORROW
from ..actions.liquidation6_single_collateral_multi_borrow2 import ACTIONS as SINGLE_COLLATERAL_MULTI_BORROW2
from ..actions.liquidation7_multi_collateral_multi_borrow import ACTIONS as MULTI_COLLATERAL_MULTI_BORROW
from ..actions.liquidation_invalid_case_1 import ACTIONS as INVALID_LIQUIDATION_CASE_1
from ..actions.liquidation_invalid_case_2 import ACTIONS as INVALID_LIQUIDATION_CASE_2
from ..actions.steps import Steps

EXA = 10 ** 18

PRECISION = 0

halfEXA = EXA // 2


def exaDiv(a: int, b: int) -> int:
    halfB = b // 2
    return (halfB + (a * EXA)) // b


def _int(_value):
    return int(_value, 0)


def _dec(_value):
    return int(_value, 0) / EXA


class LiquidationTest(OMMTestCases):
    def setUp(self):
        super().setUp()
        self.return_amount = {}

    def _transfer(self, from_, params, loan):

        if loan == "icx":
            loan = "sicx"

        tx_result = self.send_tx(
            from_=from_,
            to=loan,  # USDS contract
            method="transfer",
            params=params
        )
        return tx_result

    def _transferSICX(self, from_, to, amount):
        tx = self.send_tx(
            from_=from_,
            to=self.contracts["sicx"],
            method="transfer",
            params={
                "_to": to,
                "_value": amount}
        )

        self.assertEqual(tx['result'], 1)

    def test_01_single_collateral_single_borrow(self):
        self._execute(SINGLE_COLLATERAL_SINGLE_BORROW)
        self._verify_liquidation()

    def test_02_multi_collateral_single_borrow(self):
        self._execute(MULTI_COLLATERAL_SINGLE_BORROW)
        self._verify_liquidation()

    def test_03_single_collateral_single_borrow2(self):
        self._execute(SINGLE_COLLATERAL_SINGLE_BORROW2)
        self._verify_liquidation()

    def test_04_multi_collateral_single_borrow2(self):
        self._execute(MULTI_COLLATERAL_SINGLE_BORROW2)
        self._verify_liquidation()

    def test_05_single_collateral_multiple_borrow(self):
        self._execute(SINGLE_COLLATERAL_MULTI_BORROW)
        self._verify_liquidation()

    def test_06_single_collateral_multiple_borrow2(self):
        self._execute(SINGLE_COLLATERAL_MULTI_BORROW2)
        self._verify_liquidation()

    def test_07_multi_collateral_multi_borrow(self):
        self._execute(MULTI_COLLATERAL_MULTI_BORROW)
        self._verify_liquidation()

    def test_invalid_liquidation_case_1(self):
        self._execute(INVALID_LIQUIDATION_CASE_1)

    def test_invalid_liquidation_case_2(self):
        self._execute(INVALID_LIQUIDATION_CASE_2)

    def initialize_user(self, name):
        user = KeyWallet.create()
        self.send_icx(self.deployer_wallet, user.get_address(), 10000 * EXA)
        tx = self._transferUSDS(self.deployer_wallet, user.get_address(), 5000 * EXA)
        self.assertEqual(tx['status'], 1)
        # self._transferSICX(self.deployer_wallet, user.get_address(), 5000 * EXA)
        self.users[name] = user

    def initialize_users(self):
        self.users = {
            "admin": self.deployer_wallet,
        }
        self.initialize_user("borrower")
        self.initialize_user("liquidator")

    def _execute(self, task):
        print("\n",task["description"])

        self._price = 0.0

        self.values = {
            "before": {
                "liquidator": {},
                "reserve": {},
                "borrower": {},
            },
            "after": {
                "liquidator": {},
                "reserve": {},
                "borrower": {},
            },
            "initial": {
                "borrower": {},
            }
        }
        self.return_amount = {}
        self.initialize_users()

        for case in task["transaction"]:
            _step = case.get("_step")
            user = case.get("user") or "deployer"
            _user = self.users.get(user)
            print(f"#################################{_step} by {user}####################################")

            if _step == Steps.DEPOSIT_ICX:
                tx = self._depositICX(_user, case["amount"])
                if tx["status"] == 0:
                    print(tx["failure"])
                self.assertEqual(tx["status"], case["expectedResult"])

            elif _step == Steps.DEPOSIT_USDS:
                tx = self._depositUSDS(_user, case["amount"])
                if tx["status"] == 0:
                    print(tx["failure"])
                self.assertEqual(tx["status"], case["expectedResult"])

            elif _step == Steps.UPDATE_PRICE:
                self._update_icx_price(case)

            elif _step == Steps.BORROW_ICX or _step == Steps.BORROW_USDS:
                self._borrow(case, _user)

            elif _step == Steps.LIQUIDATION:
                borrower = self.users.get("borrower")
                liquidator = self.users.get("liquidator")
                borrower_params = {"_user": borrower.get_address()}
                liquidator_params = {"_user": liquidator.get_address()}

                ##############################
                # balance before liquidation #
                ##############################

                self._set_borrower_details("before", borrower_params)

                amount_to_liquidate = _int(
                    self.values['before']['borrower']['liquidation_data'].get("badDebt"))  # / rate

                self._set_collateral()

                self._reserve = case.get("_reserve")
                if self._reserve == "icx":
                    self._reserve = "sicx"


                print(f"PAY {self._reserve} LOAN")
                print(f"TAKE {self._collateral} COLLATERAL")

                collateral_token_address = self.contracts[self._collateral]
                reserve_token_address = self.contracts[self._reserve]

                reserve_params = {'_reserve': reserve_token_address}
                collateral_params = {'_reserve': collateral_token_address}

                self.values["before"]["liquidator"]["account_data"] = self.call_tx(
                    to=self.contracts["lendingPoolDataProvider"],
                    method="getUserAccountData",
                    params=liquidator_params)

                self._set_balance_of_liquidator("before", liquidator)

                self._set_reserve_value("before", collateral_params, reserve_params)

                ############################
                # liquidation process start#
                ############################

                liquidation_data = {'method': 'liquidationCall', 'params': {
                    '_collateral': collateral_token_address,
                    '_reserve': reserve_token_address,
                    '_user': borrower.get_address(),  # addr
                    '_purchaseAmount': amount_to_liquidate}}

                data = json.dumps(liquidation_data).encode('utf-8')

                params = {"_to": self.contracts["lendingPool"],
                          "_value": amount_to_liquidate, "_data": data}

                tx = self._transfer(liquidator, params, reserve_token_address)

                if tx.get("status") == 0:
                    print(tx)
                    print(tx["failure"])
                else:
                    self.return_amount["value"] = _int(tx['eventLogs'][7]['data'][0])

                self.assertEqual(tx["status"], case.get("expectedResult"))


                if case.get("expectedResult") == 0 and tx.get("status") == 0:
                    print("AS EXPECTED: =>", case.get("message"))
                #############################
                # balance after liquidation #
                #############################

                self._set_borrower_details("after", borrower_params)
                self.values["after"]["liquidator"]["account_data"] = self.call_tx(
                    to=self.contracts["lendingPoolDataProvider"],
                    method="getUserAccountData",
                    params=liquidator_params)
                self._set_balance_of_liquidator("after", liquidator)
                self._set_reserve_value("after", collateral_params, reserve_params)

                if case.get("errorCode") is not None:
                    self.assertEqual(tx["failure"]["code"], case.get("errorCode"))
                    self._verify_liquidation_fail()

            else:
                raise Exception("Invalid step")

    def _set_collateral(self):
        icx_collateral = 0
        usds_collateral = 0
        collaterals = self.values["before"]["borrower"]["liquidation_data"].get("collaterals")
        if collaterals is not None:
            if collaterals.get("ICX") is not None:
                icx_collateral = _int(collaterals.get("ICX").get("underlyingBalanceUSD"))
            if collaterals.get("USDs") is not None:
                usds_collateral = _int(collaterals.get("USDs").get("underlyingBalanceUSD"))
        if icx_collateral > usds_collateral:
            self._collateral = "sicx"
            self._collateral_coin = "ICX"
        else:
            self._collateral = "usds"
            self._collateral_coin = "USDs"

    def _set_reserve_value(self, key, collateral_params, reserve_params):
        self.values[key]["reserve"][self._reserve] = self.call_tx(
            to=self.contracts['lendingPoolDataProvider'],
            method="getReserveData",
            params=reserve_params)
        if self._reserve != self._collateral:
            self.values[key]["reserve"][self._collateral] = self.call_tx(
                to=self.contracts['lendingPoolDataProvider'],
                method="getReserveData",
                params=collateral_params)

    def _set_balance_of_liquidator(self, key, liquidator):
        balance_of = {}
        balance_of[self._collateral] = self.call_tx(
            to=self.contracts[self._collateral],
            method="balanceOf",
            params={"_owner": liquidator.get_address()}
        )
        balance_of[self._reserve] = self.call_tx(
            to=self.contracts[self._reserve],
            method="balanceOf",
            params={"_owner": liquidator.get_address()}
        )
        self.values[key]["liquidator"]["balanceOf"] = balance_of

    def _set_borrower_details(self, key, borrower_params):
        self.values[key]["borrower"]["account_data"] = self.call_tx(
            to=self.contracts["lendingPoolDataProvider"],
            method="getUserAccountData",
            params=borrower_params
        )
        self.values[key]["borrower"]["liquidation_data"] = self.call_tx(
            to=self.contracts["lendingPoolDataProvider"],
            method="getUserLiquidationData",
            params=borrower_params
        )

    def _verify_liquidation_fail(self):
        liquidator_before = self.values["before"]["liquidator"]
        reserve_before = self.values["before"]["reserve"]

        liquidator_after = self.values["after"]["liquidator"]
        reserve_after = self.values["after"]["reserve"]

        self.assertDictEqual(reserve_after, reserve_before)
        self.assertDictEqual(liquidator_after["balanceOf"], liquidator_before["balanceOf"])

    def _verify_liquidation(self):

        liquidator_before = self.values["before"]["liquidator"]
        borrower_before = self.values["before"]["borrower"]
        reserve_before = self.values["before"]["reserve"]

        liquidator_after = self.values["after"]["liquidator"]
        borrower_after = self.values["after"]["borrower"]
        reserve_after = self.values["after"]["reserve"]

        amount_to_liquidate = _int(self.values['before']['borrower']['liquidation_data'].get("badDebt"))

        self.assertLess(
            _int(borrower_before["account_data"].get("healthFactor")),
            _int(borrower_after["account_data"].get("healthFactor"))
        )

        self.assertGreater(
            _dec(borrower_before["liquidation_data"]["collaterals"][self._collateral_coin]["underlyingBalanceUSD"]),
            _dec(borrower_after["liquidation_data"]["collaterals"][self._collateral_coin]["underlyingBalanceUSD"])
            + amount_to_liquidate * 1.1 / EXA)

        self.assertGreaterEqual(  # =>
            _dec(borrower_before["account_data"]['totalCollateralBalanceUSD']) - amount_to_liquidate * 1.1 / EXA,
            _dec(borrower_after["account_data"]['totalCollateralBalanceUSD']), 0)

        self.assertAlmostEqual(
            _dec(borrower_before["account_data"]['totalBorrowBalanceUSD']) - amount_to_liquidate / EXA,
            _dec(borrower_after["account_data"]['totalBorrowBalanceUSD']), 4)

        self.assertAlmostEqual(
            _dec(liquidator_before["account_data"]['totalCollateralBalanceUSD']),
            _dec(liquidator_after["account_data"]['totalCollateralBalanceUSD']),
            PRECISION
        )

        self.assertAlmostEqual(
            _dec(liquidator_before["account_data"]['totalBorrowBalanceUSD']),
            _dec(liquidator_after["account_data"]['totalBorrowBalanceUSD']),
            PRECISION)

        self._validate_liquidator_balance(amount_to_liquidate, liquidator_after, liquidator_before)

        self.assertAlmostEqual(
            _dec(reserve_before[self._reserve].get("totalBorrowsUSD")),
            _dec(reserve_after[self._reserve].get("totalBorrowsUSD")) + amount_to_liquidate / EXA,
            PRECISION
        )

        if self._reserve == self._collateral:
            self.assertGreaterEqual(
                _dec(reserve_before[self._reserve].get("availableLiquidityUSD")),
                _dec(reserve_after[self._reserve].get("availableLiquidityUSD")) - amount_to_liquidate * 0.1 / EXA
            )
        else:
            self.assertAlmostEqual(
                _dec(reserve_before[self._reserve].get("availableLiquidityUSD")),
                _dec(reserve_after[self._reserve].get("availableLiquidityUSD")) - amount_to_liquidate / EXA,
                PRECISION
            )

            self.assertGreaterEqual(
                _dec(reserve_before[self._collateral].get("availableLiquidityUSD")),
                _dec(reserve_after[self._collateral].get("availableLiquidityUSD")) + amount_to_liquidate * 1.1 / EXA
            )

    def _usds_to_sicx(self, amount):

        icx_usd = _int(self.call_tx(
            to=self.contracts["priceOracle"],
            method="get_reference_data",
            params={'_base': 'ICX', '_quote': 'USD'}
        ))

        sicx_rate = _int(self.call_tx(
            to=self.contracts['staking'],
            method="getTodayRate"
        ))

        sicx = exaDiv(exaDiv(amount, icx_usd), sicx_rate)

        return sicx

    def _validate_liquidator_balance(self, amount_to_liquidate, liquidator_after, liquidator_before):
        if self._reserve == 'sicx' and self._collateral == 'sicx':
            self.assertLessEqual(_dec(liquidator_before['balanceOf'][self._reserve]),
                                 _dec(liquidator_after['balanceOf'][self._reserve]) - self._usds_to_sicx(
                                     amount_to_liquidate) * 0.1 / EXA, 0)
        elif self._reserve == self._collateral:
            self.assertLessEqual(_dec(liquidator_before['balanceOf'][self._reserve]),
                                 _dec(liquidator_after['balanceOf'][self._reserve]) - amount_to_liquidate * 0.1 / EXA)
        elif self._reserve == 'sicx':
            self.assertAlmostEqual(_dec(liquidator_before['balanceOf'][self._reserve]),
                                   _dec(liquidator_after['balanceOf'][self._reserve]) + self._usds_to_sicx(
                                       amount_to_liquidate) / EXA, 0)
            self.assertAlmostEqual(_dec(liquidator_before['balanceOf'][self._collateral]),
                                   _dec(liquidator_after['balanceOf'][
                                            self._collateral]) - amount_to_liquidate * 1.1 / EXA,
                                   PRECISION)
        elif self._collateral == 'sicx':
            self.assertAlmostEqual(_dec(liquidator_before['balanceOf'][self._reserve]),
                                   _dec(liquidator_after['balanceOf'][self._reserve]) + amount_to_liquidate / EXA,
                                   PRECISION)
            self.assertAlmostEqual(_dec(liquidator_before['balanceOf'][self._collateral]),
                                   _dec(liquidator_after['balanceOf'][self._collateral]) - self._usds_to_sicx(
                                       amount_to_liquidate) * 1.1 / EXA,
                                   0)

    def _borrow(self, case, _user):
        if case.get("_step") == Steps.BORROW_ICX:
            tx = self._borrowICX(_user, case["amount"])
        else:
            tx = self._borrowUSDS(_user, case["amount"])
        if tx["status"] == 0:
            print(tx["failure"])
        self.assertEqual(tx["status"], case["expectedResult"])
        self.values["initial"]["borrower"]["account_data"] = self.call_tx(
            to=self.contracts["lendingPoolDataProvider"],
            method="getUserAccountData",
            params={
                "_user": _user.get_address()
            })

    def _update_icx_price(self, case):
        self._price = case["rate"]
        params = {
            '_base': 'ICX',
            '_quote': 'USD',
            '_rate': case["rate"]
        }
        tx = self.send_tx(
            from_=self.deployer_wallet,
            to=self.contracts[case["contract"]],
            method=case["action"],
            params=params
        )
        self.assertEqual(tx["status"], case["expectedResult"])
        icx_usd = self.call_tx(
            to=self.contracts[case["contract"]],
            method="get_reference_data",
            params={'_base': 'ICX', '_quote': 'USD'}
        )
        print(f"1 icx = {_dec(icx_usd)} usd")
        self.assertEqual(_int(icx_usd), self._price)
