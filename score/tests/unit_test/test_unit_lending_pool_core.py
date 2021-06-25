from unittest import mock

from iconservice import Address, IconScoreException
from tbears.libs.scoretest.score_test_case import ScoreTestCase

from lendingPoolCore.Math import SECONDS_PER_YEAR
from lendingPoolCore.lendingPoolCore import LendingPoolCore

EXA = 10 ** 18

"""
https://docs.google.com/spreadsheets/d/18o_RJ4z_zSVwU8yRuzEuG9fhRHSfRoZcOEHONuEBn_g/edit?usp=sharing
"""


class TestLendingPoolCore(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_staking = Address.from_string(f"cx{'1231' * 10}")
        self.mock_dao_fund = Address.from_string(f"cx{'1232' * 10}")
        self.mock_lending_pool = Address.from_string(f"cx{'1233' * 10}")
        self.mock_delegation = Address.from_string(f"cx{'1234' * 10}")
        self.mock_liquidation_manager = Address.from_string(f"cx{'1235' * 10}")
        self._owner = self.test_account1

        lending_pool_core = self.get_score_instance(LendingPoolCore, self._owner)

        self.set_msg(self._owner, 1)
        lending_pool_core.setStaking(self.mock_staking)
        lending_pool_core.setDaoFund(self.mock_dao_fund)
        lending_pool_core.setLiquidationManager(self.mock_liquidation_manager)
        lending_pool_core.setLendingPool(self.mock_lending_pool)
        lending_pool_core.setDelegation(self.mock_delegation)

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
        self.set_msg(self._owner, 1)
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
    def sample_reserve(address: str = '0123'):
        return {
            "reserveAddress": Address.from_string(f"cx{(address + str(1)) * 8}"),
            "oTokenAddress": Address.from_string(f"cx{(address + str(2)) * 8}"),
            "dTokenAddress": Address.from_string(f"cx{(address + str(3)) * 8}"),
            "lastUpdateTimestamp": 0,
            "liquidityRate": 5 * EXA // 100,
            "borrowRate": 2 * EXA // 10,
            "liquidityCumulativeIndex": 1 * EXA,
            "borrowCumulativeIndex": 1 * EXA,
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
            self.assertIn("SenderNotScoreOwnerError", str(err))
        else:
            raise IconScoreException("Unauthorized method call", 900)

        # set admin use
        self.set_msg(self._owner, 1)
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
            "availableLiquidity": 100 * EXA,
            "totalBorrows": 10 * EXA
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
            self.lending_pool_core.updateStateOnDeposit(_reserve_address, _user_address, 100 * EXA, True)
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
            self.lending_pool_core.updateStateOnDeposit(_reserve_address, _user_address, _new_deposit, True)

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
            self.lending_pool_core.updateStateOnRedeem(_reserve_address, _user_address, redeem_amount, True)

            self.lending_pool_core.ReserveUpdated.assert_called_once()

            actual_result = self.lending_pool_core.getReserveData(_reserve_address)
            self.assertEqual(time_elapsed, actual_result["lastUpdateTimestamp"])

            self.assertAlmostEqual(0.09315789474, actual_result["borrowRate"] / EXA, 8)

            self.assertAlmostEqual(0.06729432133, actual_result["liquidityRate"] / EXA, 8)

            self.assertAlmostEqual(1.000083333, actual_result["liquidityCumulativeIndex"] / EXA, 8)
            self.assertAlmostEqual(1.000333389, actual_result["borrowCumulativeIndex"] / EXA, 8)
