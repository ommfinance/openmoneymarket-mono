from unittest import mock

from lendingPoolCore.utils.math import SECONDS_PER_YEAR
from tbears.libs.scoretest.patch.score_patcher import ScorePatcher, get_interface_score
from tbears.libs.scoretest.score_test_case import ScoreTestCase

from lendingPoolCore.lendingPoolCore import LendingPoolCore
from lendingPoolCore.utils.checks import *

EXA = 10 ** 18

"""
https://docs.google.com/spreadsheets/d/18o_RJ4z_zSVwU8yRuzEuG9fhRHSfRoZcOEHONuEBn_g/edit?usp=sharing
"""


class TestLendingPoolCore(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_address_provider = Address.from_string(f"cx{'1239' * 10}")
        self.mock_staking = Address.from_string(f"cx{'1231' * 10}")
        self.mock_fee_provider = Address.from_string(f"cx{'1232' * 10}")
        self.mock_governance = Address.from_string(f"cx{'a232' * 10}")
        self.mock_lending_pool = Address.from_string(f"cx{'1233' * 10}")
        self.mock_delegation = Address.from_string(f"cx{'1234' * 10}")
        self.mock_liquidation_manager = Address.from_string(f"cx{'1235' * 10}")
        self._owner = self.test_account1

        lending_pool_core = self.get_score_instance(LendingPoolCore, self._owner, on_install_params={
            "_addressProvider": self.mock_address_provider
        })

        self.set_msg(self.mock_address_provider)
        lending_pool_core.setAddresses(
            [{"name": LENDING_POOL, "address": self.mock_lending_pool},
             {"name": LIQUIDATION_MANAGER, "address": self.mock_liquidation_manager},
             {"name": STAKING, "address": self.mock_staking},
             {"name": FEE_PROVIDER, "address": self.mock_fee_provider},
             {"name": DELEGATION, "address": self.mock_delegation},
             {"name": GOVERNANCE, "address": self.mock_governance}]
        )

        self.lending_pool_core = lending_pool_core

        self.test_account3 = Address.from_string(f"hx{'12341' * 8}")
        self.test_account4 = Address.from_string(f"hx{'12342' * 8}")
        account_info = {
            self.test_account3: 10 ** 21,
            self.test_account4: 10 ** 21}
        self.initialize_accounts(account_info)
        self.set_msg(self.test_account3, 3)

        self._reserve = TestLendingPoolCore.sample_reserve("9876")

        # set admin use
        self.set_msg(self.mock_governance, 1)
        self.lending_pool_core.addReserveData(self._reserve)
        self._constant = {
            "reserve": self._reserve.get("reserveAddress"),
            "optimalUtilizationRate": 8 * EXA // 10,
            "baseBorrowRate": 2 * EXA // 100,
            "slopeRate1": 6 * EXA // 100,
            "slopeRate2": 1 * EXA
        }
        self.lending_pool_core.setReserveConstants([self._constant])
        self.set_msg(self.test_account4, 1)

    @staticmethod
    def sample_reserve(address: str = '0123', value=1.0):
        return {
            "reserveAddress": Address.from_string(f"cx{(address + str(1)) * 8}"),
            "oTokenAddress": Address.from_string(f"cx{(address + str(2)) * 8}"),
            "dTokenAddress": Address.from_string(f"cx{(address + str(3)) * 8}"),
            "lastUpdateTimestamp": 0,
            "liquidityRate": int(value * 0.05 * EXA),
            "borrowRate": int(value * 0.2 * EXA),
            "liquidityCumulativeIndex": int(value * 1 * EXA),
            "borrowCumulativeIndex": int(value * 1 * EXA),
            "baseLTVasCollateral": 5 * EXA // 10,
            "liquidationThreshold": 65 * EXA // 100,
            "liquidationBonus": 1 * EXA // 10,
            "decimals": 18,
            "borrowingEnabled": True,
            "usageAsCollateralEnabled": True,
            "isFreezed": False,
            "isActive": True,
        }

    def test_reserves(self):
        result = self.lending_pool_core.getReserves()
        self.assertEqual(1, len(result))

        _reserve = TestLendingPoolCore.sample_reserve()
        _reserve_address = _reserve.get("reserveAddress")
        try:
            self.lending_pool_core.addReserveData(_reserve)
        except IconScoreException as err:
            self.assertIn("SenderNotAuthorized", str(err))
        else:
            raise IconScoreException("Unauthorized method call", 900)

        # set admin use
        self.set_msg(self.mock_governance, 1)
        self.lending_pool_core.addReserveData(_reserve)

        # set normal user
        self.set_msg(self.test_account4, 1)
        result = self.lending_pool_core.getReserves()
        self.assertIn(_reserve_address, result)

        actual_result = self.lending_pool_core.getReserveData(self.test_account1)
        self.assertDictEqual(actual_result, {})

        self.patch_internal_method(_reserve_address, "balanceOf", lambda _address: 100 * EXA)
        self.patch_internal_method(_reserve.get("dTokenAddress"), "principalTotalSupply", lambda: 10 * EXA)

        actual_result = self.lending_pool_core.getReserveData(_reserve_address)
        expected_result = {**_reserve, **{
            "totalLiquidity": 110 * EXA,
            "borrowThreshold": 0,
            "availableLiquidity": 100 * EXA,
            "totalBorrows": 10 * EXA,
            "availableBorrows":0
        }}
        self.assertDictEqual(actual_result, expected_result)

    def test_normalized_income(self):
        _reserve = self._reserve
        _reserve_address = _reserve.get("reserveAddress")

        # set normal user
        self.set_msg(self.test_account4, 1)

        _totalSupply = 100 * EXA
        _totalBorrow = 10 * EXA
        self.patch_internal_method(_reserve_address, "balanceOf", lambda _address: _totalBorrow)
        self.patch_internal_method(_reserve.get("dTokenAddress"), "principalTotalSupply", lambda: _totalBorrow)

        time_elapsed = SECONDS_PER_YEAR * 10 ** 6 // 100
        with mock.patch.object(self.lending_pool_core, "now",
                               return_value=time_elapsed):
            actual_result = self.lending_pool_core.getNormalizedIncome(_reserve_address)
            self.assertEqual(10005 * EXA // 10000, actual_result)

        time_elapsed = SECONDS_PER_YEAR * 10 ** 6 // 500
        with mock.patch.object(self.lending_pool_core, "now",
                               return_value=time_elapsed):
            actual_result = self.lending_pool_core.getNormalizedIncome(_reserve_address)
            self.assertEqual(10001 * EXA // 10000, actual_result)

        time_elapsed = SECONDS_PER_YEAR * 10 ** 6 // 4
        with mock.patch.object(self.lending_pool_core, "now",
                               return_value=time_elapsed):
            actual_result = self.lending_pool_core.getNormalizedIncome(_reserve_address)
            self.assertEqual(10125 * EXA // 10000, actual_result)

    def test_normalized_debt(self):
        _reserve = self._reserve
        _reserve_address = _reserve.get("reserveAddress")

        # set normal user
        self.set_msg(self.test_account4, 1)

        _totalSupply = 500 * EXA
        _totalBorrow = 150 * EXA
        self.patch_internal_method(_reserve_address, "balanceOf", lambda _address: _totalSupply)
        self.patch_internal_method(_reserve.get("dTokenAddress"), "principalTotalSupply", lambda: _totalBorrow)

        time_elapsed = SECONDS_PER_YEAR * 10 ** 6 // 500
        with mock.patch.object(self.lending_pool_core, "now",
                               return_value=time_elapsed):
            actual_result = self.lending_pool_core.getNormalizedDebt(_reserve_address)
            self.assertAlmostEqual(1.00040008, actual_result / EXA, 7)

        time_elapsed = SECONDS_PER_YEAR * 10 ** 6 // 100
        with mock.patch.object(self.lending_pool_core, "now",
                               return_value=time_elapsed):
            actual_result = self.lending_pool_core.getNormalizedDebt(_reserve_address)
            self.assertAlmostEqual(1.002002001, actual_result / EXA, 7)

        time_elapsed = SECONDS_PER_YEAR * 10 ** 6 / 4
        with mock.patch.object(self.lending_pool_core, "now",
                               return_value=time_elapsed):
            actual_result = self.lending_pool_core.getNormalizedDebt(_reserve_address)
            self.assertAlmostEqual(1.051271095, actual_result / EXA, 7)

    def test_update_state_on_deposit_non_lending_pool(self):
        _reserve = self._reserve
        _reserve_address = _reserve.get("reserveAddress")

        _user_address = self.test_account2
        try:
            self.lending_pool_core.updateStateOnDeposit(_reserve_address, _user_address, 100 * EXA)
        except IconScoreException as err:
            self.assertIn("SenderNotAuthorized", str(err))
        else:
            raise

    def test_update_state_on_deposit(self):
        _reserve = self._reserve
        _reserve_address = _reserve.get("reserveAddress")

        _user_address = self.test_account2

        _totalSupply = 1200 * EXA
        _totalBorrow = 750 * EXA
        self.patch_internal_method(_reserve_address, "balanceOf", lambda _address: _totalSupply)
        self.patch_internal_method(_reserve.get("dTokenAddress"), "principalTotalSupply", lambda: _totalBorrow)

        # # set lending pool user
        self.set_msg(self.mock_lending_pool, 1)

        time_elapsed = SECONDS_PER_YEAR * 10 ** 6 // 100

        with mock.patch.object(self.lending_pool_core, "now",
                               return_value=time_elapsed):
            _new_deposit = 200 * EXA
            self.lending_pool_core.updateStateOnDeposit(_reserve_address, _user_address, _new_deposit)

            self.lending_pool_core.ReserveUpdated.assert_called_once()
            # self.lending_pool_core.ReserveUpdated.assert_called_with(_reserve=_reserve_address,_liquidityCumulativeIndex=10005*EXA//10000)

            # self.lending_pool_core.ReserveUpdated.assert_called_once(_reserve_address, 0.01449296917, 0.0461627907, 1.0005,
            #                                              1.002002001)

            actual_result = self.lending_pool_core.getReserveData(_reserve_address)
            self.assertEqual(time_elapsed, actual_result["lastUpdateTimestamp"])

            self.assertAlmostEqual(0.0461627907, actual_result["borrowRate"] / EXA, 8)

            self.assertAlmostEqual(0.01449296917, actual_result["liquidityRate"] / EXA, 8)

            self.assertAlmostEqual(1.0005, actual_result["liquidityCumulativeIndex"] / EXA, 8)
            self.assertAlmostEqual(1.002002001, actual_result["borrowCumulativeIndex"] / EXA, 8)

    def test_update_state_on_redeem_non_lending_pool(self):
        _reserve = self._reserve
        _reserve_address = _reserve.get("reserveAddress")

        _user_address = self.test_account2
        try:
            self.lending_pool_core.updateStateOnRedeem(_reserve_address, _user_address, 100 * EXA)
        except IconScoreException as err:
            self.assertIn("SenderNotAuthorized", str(err))
        else:
            raise

    def test_update_state_on_redeem(self):
        _reserve = self._reserve
        _reserve_address = _reserve.get("reserveAddress")

        _user_address = self.test_account2

        _totalSupply = 1750 * EXA
        _totalBorrow = 1220 * EXA
        self.patch_internal_method(_reserve_address, "balanceOf", lambda _address: _totalSupply)
        self.patch_internal_method(_reserve.get("dTokenAddress"), "principalTotalSupply", lambda: _totalBorrow)

        # # set lending pool user
        self.set_msg(self.mock_lending_pool, 1)

        time_elapsed = SECONDS_PER_YEAR * 10 ** 6 // 600

        with mock.patch.object(self.lending_pool_core, "now",
                               return_value=time_elapsed):
            redeem_amount = 1450 * EXA
            self.lending_pool_core.updateStateOnRedeem(_reserve_address, _user_address, redeem_amount)

            self.lending_pool_core.ReserveUpdated.assert_called_once()

            actual_result = self.lending_pool_core.getReserveData(_reserve_address)
            self.assertEqual(time_elapsed, actual_result["lastUpdateTimestamp"])

            self.assertAlmostEqual(0.09315789474, actual_result["borrowRate"] / EXA, 8)

            self.assertAlmostEqual(0.06729432133, actual_result["liquidityRate"] / EXA, 8)

            self.assertAlmostEqual(1.000083333, actual_result["liquidityCumulativeIndex"] / EXA, 8)
            self.assertAlmostEqual(1.000333389, actual_result["borrowCumulativeIndex"] / EXA, 8)

    def test_update_state_on_borrow_non_lending_pool(self):
        _reserve = self._reserve
        _reserve_address = _reserve.get("reserveAddress")

        _user_address = self.test_account2
        try:
            self.lending_pool_core.updateStateOnBorrow(_reserve_address, _user_address, 100 * EXA, 0)
        except IconScoreException as err:
            self.assertIn("SenderNotAuthorized", str(err))
        else:
            raise

    def test_update_state_on_borrow(self):
        _reserve = self._reserve
        _reserve_address = _reserve.get("reserveAddress")
        _d_token_address = _reserve.get("dTokenAddress")

        _user_address = self.test_account2

        _totalSupply = 1750 * EXA
        new_borrow_amount = 1450 * EXA
        _totalBorrow = (1220 + 1450) * EXA

        _user_current_borrow = 220 * EXA

        _user_interest = 100 * EXA // 1000

        self.patch_internal_method(_reserve_address, "balanceOf", lambda _address: _totalSupply)

        self._mock_debt_token_score(_totalBorrow, _user_current_borrow, _user_interest)
        # # set lending pool user
        self.set_msg(self.mock_lending_pool, 1)

        time_elapsed = SECONDS_PER_YEAR * 10 ** 6 // 600

        with mock.patch.object(self.lending_pool_core, "now",
                               return_value=time_elapsed):
            self.lending_pool_core.updateStateOnBorrow(_reserve_address, _user_address, new_borrow_amount,
                                                       10 * EXA // 100)
            prefix = self.lending_pool_core.userReservePrefix(_reserve_address, _user_address)

            self.assertEqual(time_elapsed, self.lending_pool_core.userReserve[prefix].lastUpdateTimestamp.get())
            self.assertEqual(0 + 10 * EXA // 100, self.lending_pool_core.userReserve[prefix].originationFee.get())

            self.lending_pool_core.ReserveUpdated.assert_called_once()

            mock_reserve_score = get_interface_score(_reserve_address)
            mock_reserve_score.transfer.assert_called_with(self.mock_fee_provider, _user_interest // 10)
            self.lending_pool_core.InterestTransfer(_user_interest // 10, _reserve_address, None)

            mock_d_token_score = get_interface_score(_d_token_address)

            self.assertTrue(mock_d_token_score.principalTotalSupply.called)

            mock_d_token_score.principalBalanceOf.assert_called_with(_user_address)

            mock_d_token_score.mintOnBorrow.aseert_called_with(_user_address, _user_current_borrow, _user_interest)

            self.assert_internal_call(_reserve_address, "transfer", self.mock_fee_provider, _user_interest // 10)

            actual_result = self.lending_pool_core.getReserveData(_reserve_address)

            self.assertEqual(time_elapsed, actual_result["lastUpdateTimestamp"])

            self.assertAlmostEqual(0.5749494949, actual_result["borrowRate"] / EXA, 8)
            #
            self.assertAlmostEqual(0.4651864096, actual_result["liquidityRate"] / EXA, 8)

            self.assertAlmostEqual(1.000083333, actual_result["liquidityCumulativeIndex"] / EXA, 8)
            self.assertAlmostEqual(1.000333389, actual_result["borrowCumulativeIndex"] / EXA, 8)

    def test_update_state_on_repay_non_lending_pool(self):
        _reserve = self._reserve
        _reserve_address = _reserve.get("reserveAddress")

        _user_address = self.test_account2
        try:
            self.lending_pool_core.updateStateOnRepay(_reserve_address, _user_address, 100 * EXA, True)
        except IconScoreException as err:
            self.assertIn("SenderNotAuthorized", str(err))
        else:
            raise

    def test_update_state_on_repay(self):  # fail
        _reserve = self._reserve
        _reserve_address = _reserve.get("reserveAddress")
        _d_token_address = _reserve.get("dTokenAddress")

        _user_address = self.test_account2

        _totalSupply = 2250 * EXA
        repay_amount = 920 * EXA
        _totalBorrow = (1800 - 920) * EXA
        _user_current_borrow = 920 * EXA
        borrow_balance_increase = 1 * EXA // 10

        self.patch_internal_method(_reserve_address, "balanceOf", lambda _address: _totalSupply)
        self._mock_debt_token_score(_totalBorrow, _user_current_borrow, borrow_balance_increase)
        # # set lending pool user
        self.set_msg(self.mock_lending_pool, 1)

        time_elapsed = SECONDS_PER_YEAR * 10 ** 6 // 800

        with mock.patch.object(self.lending_pool_core, "now",
                               return_value=time_elapsed):
            origination_fee = 1 * EXA // 100

            prefix = self.lending_pool_core.userReservePrefix(_reserve_address, _user_address)
            self.lending_pool_core.userReserve[prefix].originationFee.set(origination_fee)

            self.lending_pool_core.updateStateOnRepay(_reserve_address, _user_address, repay_amount, origination_fee,
                                                      borrow_balance_increase,
                                                      True)

            self.assertEqual(time_elapsed, self.lending_pool_core.userReserve[prefix].lastUpdateTimestamp.get())
            self.assertEqual(0, self.lending_pool_core.userReserve[prefix].originationFee.get())

            self.lending_pool_core.ReserveUpdated.assert_called_once()

            mock_reserve_score = get_interface_score(_reserve_address)
            mock_reserve_score.transfer.assert_called_with(self.mock_fee_provider, borrow_balance_increase // 10)
            self.lending_pool_core.InterestTransfer(borrow_balance_increase // 10, _reserve_address, None)

            mock_d_token_score = get_interface_score(_d_token_address)

            self.assertTrue(mock_d_token_score.principalTotalSupply.called)

            # mock_d_token_score.principalBalanceOf.assert_called_with(_user_address)
            mock_d_token_score.burnOnRepay.aseert_called_with(_user_address, repay_amount, borrow_balance_increase)

            self.assert_internal_call(_reserve_address, "transfer", self.mock_fee_provider,
                                      borrow_balance_increase // 10)

            actual_result = self.lending_pool_core.getReserveData(_reserve_address)

            self.assertEqual(time_elapsed, actual_result["lastUpdateTimestamp"])

            self.assertAlmostEqual(0.036296296296296300, actual_result["borrowRate"] / EXA, 8)
            #
            self.assertAlmostEqual(0.007097942386831280, actual_result["liquidityRate"] / EXA, 8)

            self.assertAlmostEqual(1.000062500000000000, actual_result["liquidityCumulativeIndex"] / EXA, 8)
            self.assertAlmostEqual(1.000250031247680000, actual_result["borrowCumulativeIndex"] / EXA, 8)

    def test_update_state_on_liquidation(self):
        _collateral_reserve = TestLendingPoolCore.sample_reserve(address="8456", value=1.6)
        self.set_msg(self.mock_governance, 1)
        self.lending_pool_core.addReserveData(_collateral_reserve)

        _collateral_reserve_address = _collateral_reserve.get("reserveAddress")
        _collateral_d_token_address = _collateral_reserve.get("dTokenAddress")

        _collateral_constant = self._constant
        _collateral_constant["reserve"] = _collateral_reserve_address
        self.lending_pool_core.setReserveConstants([self._constant, _collateral_constant])

        self.set_msg(self.test_account4, 1)

        _principal_reserve = self._reserve
        _principal_reserve_address = _principal_reserve.get("reserveAddress")
        _principal_d_token_address = _principal_reserve.get("dTokenAddress")

        _user_address = self.test_account2
        _amount_to_liquidate = 170 * EXA

        _principal_total_supply = 4500 * EXA
        _principal_total_borrow = (2500 - 170) * EXA
        _user_current_borrow = 670 * EXA

        _collateral_total_supply = 5000 * EXA
        _collateral_total_borrow = 3500 * EXA
        _user_current_collateral = 1000 * EXA

        borrow_balance_increase = 1 * EXA // 10

        self.patch_internal_method(_principal_reserve_address, "balanceOf", lambda _address: _principal_total_supply)
        self._mock_debt_token_score(_principal_total_borrow, _user_current_borrow, borrow_balance_increase)

        self.patch_internal_method(_collateral_reserve_address, "balanceOf", lambda _address: _collateral_total_supply)
        self._mock_debt_token_score(_collateral_total_borrow, 0, borrow_balance_increase, _collateral_d_token_address)

        # # set lending pool user
        self.set_msg(self.mock_liquidation_manager, 1)

        time_elapsed = SECONDS_PER_YEAR * 10 ** 6 // 800

        with mock.patch.object(self.lending_pool_core, "now",
                               return_value=time_elapsed):
            origination_fee = 1 * EXA // 100

            _principal_prefix = self.lending_pool_core.userReservePrefix(_principal_reserve_address, _user_address)
            self.lending_pool_core.userReserve[_principal_prefix].originationFee.set(origination_fee)

            _collateral_prefix = self.lending_pool_core.userReservePrefix(_collateral_reserve_address, _user_address)
            self.lending_pool_core.userReserve[_collateral_prefix].originationFee.set(origination_fee)

            self.lending_pool_core.updateStateOnLiquidation(_principal_reserve_address, _collateral_reserve_address,
                                                            _user_address,
                                                            _amount_to_liquidate, _amount_to_liquidate,
                                                            5 * EXA // 1000, 5 * EXA // 1000,
                                                            borrow_balance_increase)

            _principal_actual_result = self.lending_pool_core.getReserveData(_principal_reserve_address)
            _collateral_actual_result = self.lending_pool_core.getReserveData(_collateral_reserve_address)

            mock_principal_reserve_score = get_interface_score(_principal_reserve_address)
            mock_principal_reserve_score.transfer.assert_called_with(self.mock_fee_provider,
                                                                     borrow_balance_increase // 10)

            mock_collateral_reserve_score = get_interface_score(_collateral_reserve_address)
            self.assertTrue(mock_collateral_reserve_score.transfer.assert_not_called)

            self.lending_pool_core.InterestTransfer(borrow_balance_increase // 10, _principal_reserve_address, None)

            self.assert_internal_call(_principal_d_token_address, "burnOnLiquidation", _user_address,
                                      _amount_to_liquidate,
                                      borrow_balance_increase)

            self.assertAlmostEqual(1.000062500000000000, _principal_actual_result["liquidityCumulativeIndex"] / EXA, 8)
            self.assertAlmostEqual(1.600160000000000000, _collateral_actual_result["liquidityCumulativeIndex"] / EXA, 8)

            self.assertEqual(origination_fee - 5 * EXA // 1000,
                             self.lending_pool_core.userReserve[_principal_prefix].originationFee.get())
            self.assertEqual(time_elapsed,
                             self.lending_pool_core.userReserve[_principal_prefix].lastUpdateTimestamp.get())

            # TODO
            # self.assertEqual(origination_fee - 5 * EXA // 1000,
            #                  self.lending_pool_core.userReserve[_collateral_prefix].originationFee.get())
            # self.assertEqual(time_elapsed,
            #                  self.lending_pool_core.userReserve[_collateral_prefix].lastUpdateTimestamp.get())

            self.assertAlmostEqual(1.000250031247680000, _principal_actual_result["borrowCumulativeIndex"] / EXA, 8)
            self.assertAlmostEqual(1.600640128008830000, _collateral_actual_result["borrowCumulativeIndex"] / EXA, 8)

            self.assertEqual(time_elapsed, _principal_actual_result["lastUpdateTimestamp"])
            self.assertEqual(time_elapsed, _collateral_actual_result["lastUpdateTimestamp"])

            self.assertAlmostEqual(0.044964285714285700, _principal_actual_result["borrowRate"] / EXA, 8)
            self.assertAlmostEqual(0.051512623957157200, _collateral_actual_result["borrowRate"] / EXA, 8)

            self.assertAlmostEqual(0.013470015306122400, _principal_actual_result["liquidityRate"] / EXA, 8)
            self.assertAlmostEqual(0.019479575373700100, _collateral_actual_result["liquidityRate"] / EXA, 8)

            self.assertEqual(2, self.lending_pool_core.ReserveUpdated.call_count)

    def _mock_debt_token_score(self, total_borrow, user_borrow, interest, address: Address = None):
        token_address = self._reserve.get("dTokenAddress") if address == None else address
        self.patch_internal_method(token_address, "principalTotalSupply", lambda: total_borrow)
        ScorePatcher.patch_internal_method(token_address, "principalBalanceOf", lambda _user: user_borrow)
        ScorePatcher.patch_internal_method(token_address, "balanceOf", lambda _user: user_borrow + interest)
