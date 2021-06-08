import json
from pprint import pprint

from iconsdk.wallet.wallet import KeyWallet

from .test_integrate_omm_cases import OMMTestCases
from ..actions.liquidation_usdb_to_icx import ACTIONS as USDB_TO_ICX
from ..actions.liquidation_multi_collateral_single_borrow import ACTIONS as MULTI_COLLATERAL_SINGLE_BORROW
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
            to=loan,  # USDB contract
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

    def test_usdb_to_icx_liquidation(self):
        self._execute(USDB_TO_ICX)
        self._verify_liquidation()

    def test_multi_collateral_single_borrow(self):
        self._execute(MULTI_COLLATERAL_SINGLE_BORROW)
        self._verify_liquidation()


    def initialize_user(self, name):
        user = KeyWallet.create()
        self.send_icx(self.deployer_wallet, user.get_address(), 10000 * EXA)
        tx = self._transferUSDB(self.deployer_wallet, user.get_address(), 5000 * EXA)
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
        print(task["description"])

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

            elif _step == Steps.DEPOSIT_USDB:
                tx = self._depositUSDB(_user, case["amount"])
                if tx["status"] == 0:
                    print(tx["failure"])
                self.assertEqual(tx["status"], case["expectedResult"])

            elif _step == Steps.UPDATE_PRICE:
                self._update_icx_price(case)

            elif _step == Steps.BORROW_ICX or _step == Steps.BORROW_USBD:
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

                print("self._collateral", self._collateral)
                print("self._reserve", self._reserve)

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
                    print(tx["failure"])
                else:
                    pprint(tx)
                    self.return_amount["value"] = _int(tx['eventLogs'][7]['data'][0])

                self.assertEqual(tx["status"], case.get("expectedResult"))

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

            else:
                raise Exception("Invalid step")

        pprint(self.values)

    def _set_collateral(self):
        icx_collateral = 0
        usdb_collateral = 0
        collaterals = self.values["before"]["borrower"]["liquidation_data"].get("collaterals")
        if collaterals is not None:
            if collaterals.get("ICX") is not None:
                icx_collateral = _int(collaterals.get("ICX").get("underlyingBalanceUSD"))
            if collaterals.get("USDb") is not None:
                usdb_collateral = _int(collaterals.get("USDb").get("underlyingBalanceUSD"))
        if icx_collateral > usdb_collateral:
            self._collateral = "sicx"
            self._collateral_coin = "ICX"
        else:
            self._collateral = "usdb"
            self._collateral_coin = "USDb"

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

    def _usdb_to_sicx(self, amount):

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
                                 _dec(liquidator_after['balanceOf'][self._reserve]) - self._usdb_to_sicx(
                                     amount_to_liquidate) * 0.1 / EXA, 0)
        elif self._reserve == self._collateral:
            self.assertLessEqual(_dec(liquidator_before['balanceOf'][self._reserve]),
                                 _dec(liquidator_after['balanceOf'][self._reserve]) - amount_to_liquidate * 0.1 / EXA)
        elif self._reserve == 'sicx':
            self.assertAlmostEqual(_dec(liquidator_before['balanceOf'][self._reserve]),
                                   _dec(liquidator_after['balanceOf'][self._reserve]) + self._usdb_to_sicx(
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
                                   _dec(liquidator_after['balanceOf'][self._collateral]) - self._usdb_to_sicx(
                                       amount_to_liquidate) * 1.1 / EXA,
                                   0)

    def _borrow(self, case, _user):
        if case.get("_step") == Steps.BORROW_ICX:
            tx = self._borrowICX(_user, case["amount"])
        else:
            tx = self._borrowUSDB(_user, case["amount"])
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
        print("icx_usd", icx_usd)
        self.assertEqual(_int(icx_usd), self._price)
