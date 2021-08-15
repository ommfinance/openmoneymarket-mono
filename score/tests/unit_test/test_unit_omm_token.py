import os
from unittest import mock

from iconservice import Address, IconScoreException, AddressPrefix
from tbears.libs.scoretest.patch.score_patcher import get_interface_score
from tbears.libs.scoretest.score_test_case import ScoreTestCase

from rewardDistribution.utils.checks import *
from ommToken.omm import OmmToken
from ommToken.tokens.IRC2 import Status

EXA = 10 ** 18
TIME = 10 ** 6


def create_address(prefix: AddressPrefix = AddressPrefix.EOA) -> 'Address':
    return Address.from_bytes(prefix.to_bytes(1, 'big') + os.urandom(20))


class TestOmmToken(ScoreTestCase):

    def setUp(self):
        super().setUp()
        self._owner = self.test_account1
        self.score = self.get_score_instance(OmmToken, self._owner)

        self.mock_reward_distribution = Address.from_string(f"cx{'1231' * 10}")
        self.mock_delegation = Address.from_string(f"cx{'1232' * 10}")
        self.mock_lending_pool = Address.from_string(f"cx{'1233' * 10}")

        self.set_tx(origin=self._owner)
        self.score.setAddresses([
            {"name": 'lendingPool', "address": self.mock_lending_pool},
            {"name": "delegation", "address": self.mock_delegation},
            {"name": "rewards", "address": self.mock_reward_distribution}
        ])

        self.test_account3 = create_address()
        self.test_account4 = create_address()
        account_info = {self.test_account3: 10 ** 21,
                        self.test_account4: 10 ** 21}
        ScoreTestCase.initialize_accounts(account_info)

    def test_mint_unauthorized_call(self):
        try:
            self.set_msg(self.test_account3)
            self.score.mint(10 * EXA)
        except IconScoreException as err:
            self.assertIn("SenderNotAuthorized", str(err))
        else:
            raise IconScoreException("Unauthorized call")

        try:
            self.set_msg(self._owner)
            self.score.mint(10 * EXA)
        except IconScoreException as err:
            self.assertIn("SenderNotAuthorized", str(err))
        else:
            raise IconScoreException("Unauthorized call")

    def test_mint(self):
        self.set_msg(self._owner)
        self.score.setUnstakingPeriod(102)

        self.register_interface_score(self.mock_reward_distribution)

        with mock.patch.object(self.score, "now", return_value=101 * TIME):
            self.set_msg(self.mock_reward_distribution)
            self.score.mint(10 * EXA)

            self.assertEqual(10 * 10 ** 18, self.score._total_supply.get())
            self.assertEqual(0, self.score._balances[self.score.address])
            self.assertEqual(10 * 10 ** 18, self.score._balances[self.mock_reward_distribution])

            self.score.Mint.assert_called_with(10 * EXA, b'minted by reward')
            self.score.Transfer.assert_called_with(ZERO_SCORE_ADDRESS, self.mock_reward_distribution, 10 * EXA,
                                                   b'minted by reward')

    def test_add_to_lockList(self):

        _user = self.test_account3
        # GIVEN
        self.set_msg(self._owner)
        self.score.setUnstakingPeriod(100)

        self.score._staked_balances[_user][Status.AVAILABLE] = 0
        self.score._staked_balances[_user][Status.STAKED] = 30 * EXA
        self.score._staked_balances[_user][Status.UNSTAKING] = 20 * EXA
        self.score._staked_balances[_user][Status.UNSTAKING_PERIOD] = 100 * TIME
        self.score._total_staked_balance.set(30 * EXA)
        self.set_msg(self.test_account3)
        try:
            self.score.add_to_lockList(self.test_account3)
        except IconScoreException as err:
            self.assertIn("SenderNotScoreOwnerError", str(err))
        else:
            raise IconScoreException("Unauthorized method call")

        self.set_msg(self._owner)
        with mock.patch.object(self.score, "now", return_value=101 * TIME):
            self.score.add_to_lockList(_user)

            self.assertEqual(0, self.score._total_staked_balance.get())
            self.assertEqual(20 * EXA, self.score._staked_balances[_user][Status.AVAILABLE])
            self.assertEqual(30 * EXA, self.score._staked_balances[_user][Status.UNSTAKING])
            self.assertEqual(0, self.score._staked_balances[_user][Status.STAKED])
            self.assertEqual(201 * TIME, self.score._staked_balances[_user][Status.UNSTAKING_PERIOD])

            self.assertEqual([_user], self.score.get_locklist_addresses())

    def test_remove_from_lockList(self):

        _user = self.test_account3
        # GIVEN
        self.score._lock_list.put(_user)
        self.score._lock_list.put(self.test_account4)
        self.set_msg(self.test_account4)
        try:
            self.score.remove_from_lockList(self.test_account3)
        except IconScoreException as err:
            self.assertIn("SenderNotScoreOwnerError", str(err))
        else:
            raise IconScoreException("Unauthorized method call")

        self.set_msg(self._owner)
        self.score.remove_from_lockList(_user)

        self.assertEqual([self.test_account4], self.score.get_locklist_addresses())

    def test_transfer_should_fail_if_user_in_lock_list(self):
        _user = self.test_account3
        self.score._lock_list.put(_user)
        self.set_msg(_user)
        try:
            self.score.transfer(self.test_account4, 10 * EXA)
        except IconScoreException as err:
            self.assertIn(" is locked", str(err))
        else:
            raise IconScoreException("Token transferred even user is in lock list")

    def test_transfer_should_able_to_transfer(self):
        _user = self.test_account3
        # GIVEN
        self.set_msg(self._owner)
        self.score.setUnstakingPeriod(100)

        self.score._staked_balances[_user][Status.AVAILABLE] = 0
        self.score._staked_balances[_user][Status.STAKED] = 20 * EXA
        self.score._staked_balances[_user][Status.UNSTAKING] = 20 * EXA
        self.score._staked_balances[_user][Status.UNSTAKING_PERIOD] = 100 * TIME
        self.score._balances[_user] = 40 * EXA
        self.score._total_supply.set(40 * EXA)

        self.set_msg(_user)

        with mock.patch.object(self.score, "now", return_value=100 * TIME):
            self.score.transfer(self.test_account4, 10 * EXA)

            self.assertEqual(40 * EXA, self.score._total_supply.get())

            self.assertEqual(30 * EXA, self.score._balances[_user])
            self.assertEqual(10 * EXA, self.score._balances[self.test_account4])

            self.assertEqual(10 * EXA, self.score._staked_balances[_user][Status.AVAILABLE])
            self.assertEqual(10 * EXA, self.score._staked_balances[self.test_account4][Status.AVAILABLE])

            self.score.Transfer.assert_called_with(_user, self.test_account4, 10 * EXA,
                                                   b'None')

    def test_staking_not_authorized(self):
        self.set_msg(self._owner)
        try:
            self.score.stake(10 * EXA, self.test_account4)
        except IconScoreException as err:
            self.assertIn("SenderNotAuthorized", str(err))
        else:
            raise IconScoreException("Unauthorized method call")

    def test_staking_validation(self):
        # GIVEN
        _user = self.test_account3
        self.set_msg(self._owner)
        self.score.setMinimumStake(5 * EXA)
        self.score._balances[_user] = 18 * EXA

        self.set_msg(self.mock_lending_pool)
        try:
            self.score.stake(-1, _user)
        except IconScoreException as err:
            self.assertIn("Cannot stake less than zerovalue to stake", str(err))
        else:
            raise IconScoreException("Invalid staking value")

        try:
            self.score.stake(4 * EXA, _user)
        except IconScoreException as err:
            self.assertIn("is smaller the minimum stake", str(err))
        else:
            raise IconScoreException("Invalid staking value")

        # Insufficient balance
        self.score._staked_balances[_user][Status.AVAILABLE] = 4 * EXA
        self.score._staked_balances[_user][Status.STAKED] = 8 * EXA
        self.score._staked_balances[_user][Status.UNSTAKING] = 6 * EXA
        self.score._staked_balances[_user][Status.UNSTAKING_PERIOD] = 100 * TIME
        try:
            with mock.patch.object(self.score, "now", return_value=99 * TIME):
                self.score.stake(13 * EXA, _user)
        except IconScoreException as err:
            self.assertIn("user dont have enough balanceamount to stake", str(err))
        else:
            raise IconScoreException("Insufficient balance staked")

        try:
            with mock.patch.object(self.score, "now", return_value=99 * TIME):
                self.score.stake(7 * EXA, _user)
        except IconScoreException as err:
            self.assertIn("Stake amount less than previously staked value", str(err))
        else:
            raise IconScoreException("Stake amount less than previously staked value")

        # LOCKED user

        self.score._lock_list.put(_user)
        try:
            with mock.patch.object(self.score, "now", return_value=99 * TIME):
                self.score.stake(11 * EXA, _user)
        except IconScoreException as err:
            self.assertIn("is locked", str(err))
        else:
            raise IconScoreException("Staked by locked user")

    def test_staking(self):
        # GIVEN
        _user = self.test_account3
        seconds_in_day = 60 * 60 * 24
        self.set_msg(self._owner)
        self.score.setUnstakingPeriod(3 * seconds_in_day)
        self.score.setMinimumStake(5 * EXA)
        self.register_interface_score(self.mock_delegation)
        self.register_interface_score(self.mock_reward_distribution)

        self.score._staked_balances[_user][Status.AVAILABLE] = 10 * EXA
        self.score._staked_balances[_user][Status.STAKED] = 20 * EXA
        self.score._staked_balances[_user][Status.UNSTAKING] = 30 * EXA
        self.score._staked_balances[_user][Status.UNSTAKING_PERIOD] = seconds_in_day * TIME

        self.score._balances[_user] = 60 * EXA
        self.score._total_supply.set(60 * EXA)
        self.score._total_staked_balance.set(20 * EXA)

        self.set_msg(self.mock_lending_pool)
        with mock.patch.object(self.score, "now", return_value=15 * seconds_in_day * TIME // 10):
            self.score.stake(30 * EXA, _user)

            self.assertEqual(30 * EXA, self.score._staked_balances[_user][Status.AVAILABLE])
            self.assertEqual(30 * EXA, self.score._staked_balances[_user][Status.STAKED])
            self.assertEqual(0, self.score._staked_balances[_user][Status.UNSTAKING])
            self.assertEqual(seconds_in_day * TIME,
                             self.score._staked_balances[_user][Status.UNSTAKING_PERIOD])
            self.assertEqual(30 * EXA, self.score._total_staked_balance.get())

            mock_score = get_interface_score(self.mock_delegation)
            mock_score.updateDelegations(_user=_user)
            self.assert_internal_call(self.mock_reward_distribution, "handleAction", _user, 20 * EXA, 20 * EXA)

    def test_unstake_not_authorized(self):
        self.set_msg(self._owner)
        try:
            self.score.unstake(10 * EXA, self.test_account4)
        except IconScoreException as err:
            self.assertIn("SenderNotAuthorized", str(err))
        else:
            raise IconScoreException("Unauthorized method call")

    def test_unstake_validation(self):
        # GIVEN
        _user = self.test_account3
        self.set_msg(self._owner)
        self.score.setMinimumStake(5 * EXA)
        self.score._balances[_user] = 18 * EXA

        self.set_msg(self.mock_lending_pool)
        try:
            self.score.unstake(-1, _user)
        except IconScoreException as err:
            self.assertIn("Cannot unstake less than zero", str(err))
        else:
            raise IconScoreException("Invalid unstaking value")
        # Insufficient staking
        self.score._staked_balances[_user][Status.AVAILABLE] = 4 * EXA
        self.score._staked_balances[_user][Status.STAKED] = 8 * EXA
        self.score._staked_balances[_user][Status.UNSTAKING] = 6 * EXA
        self.score._staked_balances[_user][Status.UNSTAKING_PERIOD] = 100 * TIME

        try:
            with mock.patch.object(self.score, "now", return_value=99 * TIME):
                self.score.unstake(9 * EXA, _user)
        except IconScoreException as err:
            self.assertIn("Cannot unstake,user dont have enough staked  balance", str(err))
        else:
            raise IconScoreException("Invalid staking value")

        try:
            with mock.patch.object(self.score, "now", return_value=99 * TIME):
                self.score.unstake(5 * EXA, _user)
        except IconScoreException as err:
            self.assertIn("you already have a unstaking order,try after the amount is unstaked", str(err))
        else:
            raise IconScoreException("Already unstake in progress")

        # LOCKED user

        self.score._lock_list.put(_user)
        try:
            with mock.patch.object(self.score, "now", return_value=99 * TIME):
                self.score.unstake(8 * EXA, _user)
        except IconScoreException as err:
            self.assertIn("is locked", str(err))
        else:
            raise IconScoreException("Staked by locked user")

    def test_unstake(self):
        # GIVEN
        _user = self.test_account3
        seconds_in_day = 60 * 60 * 24
        self.set_msg(self._owner)
        self.score.setUnstakingPeriod(3 * seconds_in_day)
        self.score.setMinimumStake(5 * EXA)

        self.register_interface_score(self.mock_delegation)
        self.register_interface_score(self.mock_reward_distribution)

        self.score._staked_balances[_user][Status.AVAILABLE] = 10 * EXA
        self.score._staked_balances[_user][Status.STAKED] = 20 * EXA
        self.score._staked_balances[_user][Status.UNSTAKING] = 30 * EXA
        self.score._staked_balances[_user][Status.UNSTAKING_PERIOD] = seconds_in_day * TIME

        self.score._balances[_user] = 60 * EXA
        self.score._total_supply.set(60 * EXA)
        self.score._total_staked_balance.set(30 * EXA)

        self.set_msg(self.mock_lending_pool)
        with mock.patch.object(self.score, "now", return_value=25 * seconds_in_day * TIME // 10):
            self.score.unstake(20 * EXA, _user)

            self.assertEqual(40 * EXA, self.score._staked_balances[_user][Status.AVAILABLE])
            self.assertEqual(0, self.score._staked_balances[_user][Status.STAKED])
            self.assertEqual(20 * EXA, self.score._staked_balances[_user][Status.UNSTAKING])
            self.assertEqual(55 * seconds_in_day * TIME // 10,
                             self.score._staked_balances[_user][Status.UNSTAKING_PERIOD])
            self.assertEqual(10 * EXA, self.score._total_staked_balance.get())

            mock_score = get_interface_score(self.mock_delegation)
            mock_score.updateDelegations(_user=_user)

            self.assert_internal_call(self.mock_reward_distribution, "handleAction", _user, 20 * EXA, 30 * EXA)
