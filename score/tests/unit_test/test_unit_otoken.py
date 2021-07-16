from unittest import mock

from iconservice import Address, IconScoreException
from tbears.libs.scoretest.patch.score_patcher import get_interface_score, ScorePatcher
from tbears.libs.scoretest.score_test_case import ScoreTestCase

from score.oToken.oToken import OToken


class TestOToken(ScoreTestCase):
    def setUp(self):
        super().setUp()
        self.mock_liquidation = Address.from_string(f"cx{'1231' * 10}")
        self.mock_reserve = Address.from_string(f"cx{'1232' * 10}")
        self.mock_lendingdata_provider = Address.from_string(f"cx{'1233' * 10}")
        self.mock_lendingpool_core = Address.from_string(f"cx{'1234' * 10}")
        self.mock_lendingpool = Address.from_string(f"cx{'1235' * 10}")
        self.mock_distributionmanager = Address.from_string(f"cx{'1236' * 10}")
        self._owner = self.test_account1
        score = self.get_score_instance(OToken, self._owner,
                                        on_install_params={"_name": "OToken", "_symbol": 'ot', "_decimals": 18})

        self.score = score
        self.set_msg(self._owner)
        self.score.setLiquidation(self.mock_liquidation)
        self.score.setReserve(self.mock_reserve)
        self.score.setLendingPoolDataProvider(self.mock_lendingdata_provider)
        self.score.setLendingPoolCore(self.mock_lendingpool_core)
        self.score.setLendingPool(self.mock_lendingpool)
        self.score.setDistributionManager(self.mock_distributionmanager)

    def test_name(self):
        expected_result = "OToken"
        actual_result = self.score.name()
        self.assertEqual(expected_result, actual_result)

    def test_symbol(self):
        expected_result = "ot"
        actual_result = self.score.symbol()
        self.assertEqual(expected_result, actual_result)

    def test_principal_total_supply(self):
        self.score._totalSupply.set(20*10**18)
        self.score.principalTotalSupply()
        # print("The total supply is ",self.score.principalTotalSupply())

    def test_total_supply(self):
        self.score._totalSupply.set(100 * 10 ** 18)

        self.patch_internal_method(self.mock_lendingpool_core, "getReserveLiquidityCumulativeIndex",
                                   lambda _a: 50 * 10 ** 18)  # called from score

        ScorePatcher.patch_internal_method(self.mock_lendingpool_core, "getNormalizedIncome", lambda _a: 30 * 10 ** 18)

        actual_total_supply = self.score.totalSupply()
        # print(actual_total_supply)

        self.assertEqual((100 * 30) / 50, actual_total_supply / 10 ** 18)
        self.assert_internal_call(self.mock_lendingpool_core, "getReserveLiquidityCumulativeIndex", self.mock_reserve)
        self.assert_internal_call(self.mock_lendingpool_core, "getNormalizedIncome", self.mock_reserve)

    def test_total_supply_BI_0(self):
        self.score._totalSupply.set(100 * 10 ** 18)
        self.patch_internal_method(self.mock_lendingpool_core, "getReserveLiquidityCumulativeIndex",
                                   lambda _a: 0 * 10 ** 18)  # called from score

        actual_total_supply = self.score.totalSupply()
        # print(actual_total_supply)
        self.assertEqual(100, actual_total_supply / 10 ** 18)
        self.assert_internal_call(self.mock_lendingpool_core, "getReserveLiquidityCumulativeIndex", self.mock_reserve)

    def test_mint_lees_than_zero(self):
        _amount = -1
        _user_account = self.test_account1
        try:
            self.score._mint(_user_account, _amount)
        except IconScoreException as err:
            self.assertIn("Invalid value: -1 to mint", str(err))

    def test_mint_on_deposit(self):
        _amount = 100 * 10 ** 18
        _user_balance = 10 * 10 ** 18
        _user_account = self.test_account1

        self.score._totalSupply.set(_amount)
        self.score._balances[_user_account] = _user_balance

        self.patch_internal_method(self.mock_lendingpool_core, "getNormalizedIncome", lambda _a: 30 * 10 ** 18)
        self.patch_internal_method(self.mock_distributionmanager, "_distributionManager", lambda _a: 3)
        self.set_msg(self.mock_lendingpool)
        self.score.mintOnDeposit(_user_account, 10 * 10 ** 18)

        self.assertEqual(20 * 10 ** 18, self.score._balances[_user_account])
        self.assertEqual(110 * 10 ** 18, self.score._totalSupply.get())

        self.score.Transfer.assert_called_with(Address.from_string("cx0000000000000000000000000000000000000000") , _user_account,
                                               10 * 10 ** 18, b'mint')
        self.score.Mint.assert_called_with(_user_account, 10 * 10 ** 18)

    def test_burn_lees_than_zero(self):
        _amount = -1
        _user_account = self.test_account1
        try:
            self.score._burn(_user_account, _amount)
        except IconScoreException as err:
            self.assertIn("Invalid value: -1 to burn", str(err))

    def test_burn_on_liquidation(self):
        _amount = 100 * 10 ** 18
        _user_balance = 100 * 10 ** 18
        _user_account = self.test_account1

        self.score._totalSupply.set(_amount)
        self.score._balances[_user_account] = _user_balance

        self.patch_internal_method(self.mock_lendingpool_core, "getNormalizedIncome", lambda _a: 30 * 10 ** 18)
        self.patch_internal_method(self.mock_distributionmanager, "_distributionManager", lambda _a: 3)
        self.set_msg(self.mock_liquidation)
        self.score.burnOnLiquidation(_user_account, 10 * 10 ** 18)

        self.assertEqual(90 * 10 ** 18, self.score._balances[_user_account])
        self.assertEqual(90 * 10 ** 18, self.score._totalSupply.get())

        self.score.Transfer.assert_called_with(_user_account, Address.from_string("cx0000000000000000000000000000000000000000"),
                                               10 * 10 ** 18, b'burn')
        self.score.Burn.assert_called_with(_user_account, 10 * 10 ** 18)

    def test_is_transfer_allowed(self):
        self.patch_internal_method(self.mock_lendingdata_provider, "balanceDecreaseAllowed", lambda _a, _b, _c: True)
        # ScorePatcher.patch_internal_method()
        actual_result = self.score.isTransferAllowed(self.test_account2, 100 * 10 ** 18)

        self.assertEqual(True, actual_result)

        mock_lending_data_provider_score = get_interface_score(self.mock_lendingdata_provider)

        mock_lending_data_provider_score.balanceDecreaseAllowed.assert_called_with(self.mock_reserve,
                                                                                   self.test_account2, 100 * 10 ** 18)

        self.assert_internal_call(self.mock_lendingdata_provider, "balanceDecreaseAllowed", self.mock_reserve,
                                  self.test_account2, 100 * 10 ** 18)

    def test_transfer_less_zero(self):
        _amount = -1
        _sender_account = self.test_account1
        _receiver_account = self.test_account2
        try:
            self.score._transfer(_sender_account,_receiver_account,_amount,"less than zero")
        except IconScoreException as err:
            self.assertIn("Transferring value:-1 cannot be less than 0.",str(err))

    def test_transfer_less_than_balance(self):
        _sender_account = self.test_account1
        _sender_balances = self.score._balances[_sender_account]
        _amount = 5 * 10 **18
        _receiver_account = self.test_account2
        try:
            self.score._transfer(_sender_account,_receiver_account,_amount,"less than balance")
        except IconScoreException as err:
            self.assertIn("Token transfer error:Insufficient balance:0",str(err))

    # def test_transfer(self):




