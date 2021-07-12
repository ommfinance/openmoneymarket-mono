import os
from unittest import mock

from iconservice import Address, IconScoreException, AddressPrefix
from tbears.libs.scoretest.score_test_case import ScoreTestCase

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
        self._admin = self.test_account2
        self.score = self.get_score_instance(OmmToken, self._owner)

        self.mock_rewards = Address.from_string(f"cx{'1231' * 10}")
        self.mock_delegation = Address.from_string(f"cx{'1232' * 10}")
        self.mock_lengding_pool = Address.from_string(f"cx{'1233' * 10}")

        self.set_msg(self._owner)
        self.score.setAdmin(self._admin)

        self.score.setRewards(self.mock_rewards)
        self.score.setDelegation(self.mock_delegation)
        self.score.setLendingPool(self.mock_lengding_pool)

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

        self.score.setUnstakingPeriod(102)

        self.register_interface_score(self.mock_rewards)

        with mock.patch.object(self.score, "now", return_value=101 * TIME):
            self.set_msg(self._admin)
            self.score.mint(10 * EXA)

            self.assertEqual(10 * 10 ** 18, self.score._total_supply.get())
            self.assertEqual(0, self.score._balances[self.score.address])
            self.assertEqual(10 * 10 ** 18, self.score._balances[self.mock_rewards])

            self.assertEqual(0, self.score._staked_balances[self.score.address][Status.AVAILABLE])
            self.assertEqual(10 * 10 ** 18, self.score._staked_balances[self.mock_rewards][Status.AVAILABLE])

            self.assert_internal_call(self.mock_rewards, "tokenFallback", self.score.address, 10 * EXA,
                                      b'Transferred to Rewards SCORE')
            self.score.Mint.assert_called_with(10 * EXA, b'None')
            self.score.Transfer.assert_called_with(self.score.address, self.mock_rewards, 10 * EXA,
                                                   b'Transferred to Rewards SCORE')

    def test_add_to_lockList(self):

        _user = self.test_account3
        # GIVEN
        self.score.setUnstakingPeriod(100)

        self.score._staked_balances[_user][Status.AVAILABLE] = 0
        self.score._staked_balances[_user][Status.STAKED] = 30 * EXA
        self.score._staked_balances[_user][Status.UNSTAKING] = 20 * EXA
        self.score._staked_balances[_user][Status.UNSTAKING_PERIOD] = 100 * TIME
        self.score._total_staked_balance.set(30 * EXA)
        self.set_msg(self._admin)
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
        self.set_msg(self._admin)
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
