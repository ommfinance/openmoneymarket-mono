import os

from iconservice import Address, IconScoreException, AddressPrefix
from tbears.libs.scoretest.score_test_case import ScoreTestCase

from ommToken.tokens.IRC2 import Status
from stakedLp.stakedLp import StakedLp

EXA = 10 ** 18


def create_address(prefix: AddressPrefix = AddressPrefix.EOA) -> 'Address':
    return Address.from_bytes(prefix.to_bytes(1, 'big') + os.urandom(20))


class TestStakedLP(ScoreTestCase):

    def setUp(self):
        super().setUp()
        self._owner = self.test_account1
        self._admin = self.test_account2
        self.score = self.get_score_instance(StakedLp, self._owner)

        self.mock_dex = Address.from_string(f"cx{'1231' * 10}")
        self.mock_reward = Address.from_string(f"cx{'1232' * 10}")

        self.set_tx(origin=self._owner)
        self.score.setAddresses([
            {"name": 'dex', "address": self.mock_dex},
            {"name": "rewards", "address": self.mock_reward}
        ])

        self.test_account3 = create_address()
        self.test_account4 = create_address()
        account_info = {self.test_account3: 10 ** 21,
                        self.test_account4: 10 ** 21}
        ScoreTestCase.initialize_accounts(account_info)

    def test_unstaking_period(self):
        try:
            self.set_msg(self.test_account3)
            self.score.setUnstakingPeriod(10)
        except IconScoreException as err:
            self.assertIn("SenderNotScoreOwnerError", str(err))
        else:
            raise IconScoreException("Unauthorized call")

        self.set_msg(self._owner)
        self.score.setUnstakingPeriod(10)

        self.assertEqual(10 * 10 ** 6, self.score.getUnstakingPeriod())

    def test_balance_of(self):
        # GIVEN
        _from = create_address(AddressPrefix.CONTRACT)
        _pool_id = 1
        self.score._poolStakeDetails[_from][_pool_id][Status.AVAILABLE] = 0 * EXA
        self.score._poolStakeDetails[_from][_pool_id][Status.STAKED] = 0 * EXA
        self.patch_internal_method(self.mock_dex, "balanceOf", lambda _a, _b: 100 * EXA)
        self.score._totalStaked[_pool_id] = 10 * EXA

        actual_result = self.score.balanceOf(_from, _pool_id)

        self.assertDictEqual({
            "poolID": _pool_id,
            "userTotalBalance": 100 * EXA,
            "userAvailableBalance": 100 * EXA,
            "userStakedBalance": 0,
            "totalStakedBalance": 10 * EXA
        }, actual_result)

        self.assert_internal_call(self.mock_dex, "balanceOf", _from, _pool_id)

    def test_detail_balance_of(self):
        # GIVEN
        _user = create_address(AddressPrefix.CONTRACT)
        _pool_id1 = 1
        self.score._poolStakeDetails[_user][_pool_id1][Status.STAKED] = 11 * EXA
        self.score._totalStaked[_pool_id1] = 26 * EXA

        _pool_id2 = 2
        self.score._poolStakeDetails[_user][_pool_id2][Status.STAKED] = 25 * EXA
        self.score._totalStaked[_pool_id2] = 21 * EXA

        self.patch_internal_method(self.mock_dex, "balanceOf", lambda _a, _b: 100 * EXA)
        self.score._supportedPools.put(_pool_id1)
        self.score._supportedPools.put(_pool_id2)

        # Execute
        actual_result = self.score.getPoolBalanceByUser(_user)

        expected_result = [{
            "poolID": _pool_id1,
            "userTotalBalance": 111 * EXA,
            "userAvailableBalance": 100 * EXA,
            "userStakedBalance": 11 * EXA,
            "totalStakedBalance": 26 * EXA
        }, {
            "poolID": _pool_id2,
            "userTotalBalance": 125 * EXA,
            "userAvailableBalance": 100 * EXA,
            "userStakedBalance": 25 * EXA,
            "totalStakedBalance": 21 * EXA
        }]

        self.assertEqual(expected_result, actual_result)

    def test_on_IRC31_Received_unauthorized_call(self):
        try:
            _user = self.test_account3
            _data = '{"method": "unstake"}'.encode("utf-8")
            self.set_msg(self._owner)
            self.score.onIRC31Received(_from=_user, _id=1, _value=10 * EXA, _data=_data)
        except IconScoreException as err:
            self.assertIn("SenderNotAuthorized", str(err))
        else:
            raise IconScoreException("Unauthorized call")

    def test_on_IRC31_Received_unknown_method(self):
        try:
            _user = self.test_account3
            _data = '{"method": "unstake"}'.encode("utf-8")
            self.set_msg(self.mock_dex)
            self.score.onIRC31Received(_operator=self._owner, _from=_user, _id=1, _value=10 * EXA, _data=_data)
        except IconScoreException as err:
            self.assertIn("No valid method called", str(err))
        else:
            raise IconScoreException("Invalid method argument")

    def test_on_IRC31_Received_validate(self):
        # GIVEN
        self.set_msg(self._owner)
        self.score.setMinimumStake(100 * EXA)
        _pool_id = 1
        _user = self.test_account3
        self.score._poolStakeDetails[_user][_pool_id][Status.STAKED] = 102 * EXA
        self.score._totalStaked[_pool_id] = 120 * EXA

        _data = '{"method": "stake"}'.encode("utf-8")
        self.set_msg(self.mock_dex)
        # Not supported pool
        try:
            self.score.onIRC31Received(_operator=self._owner, _from=_user, _id=1, _value=10 * EXA, _data=_data)
        except IconScoreException as err:
            self.assertIn("is not supported", str(err))
        else:
            raise IconScoreException("Not supported pool")

        # GIVEN
        self.score._supportedPools.put(1)

        try:
            self.score.onIRC31Received(_operator=self._owner, _from=_user, _id=1, _value=-10 * EXA, _data=_data)
        except IconScoreException as err:
            self.assertIn("Cannot stake less than zero", str(err))
        else:
            raise IconScoreException("Not supported stake value::1")

        # invalid minimum stake
        try:
            self.score.onIRC31Received(_operator=self._owner, _from=_user, _id=1, _value=99 * EXA, _data=_data)
        except IconScoreException as err:
            self.assertIn("is smaller the minimum stake", str(err))
        else:
            raise IconScoreException("Not supported stake value::2")

        # new stake value is less that previous staked
        self.patch_internal_method(self.mock_dex, "balanceOf", lambda _a, _b: 111 * EXA)
        try:
            self.score.onIRC31Received(_operator=self._owner, _from=_user, _id=1, _value=101 * EXA, _data=_data)
        except IconScoreException as err:
            self.assertIn("Stake amount less than previously staked value", str(err))
        else:
            raise IconScoreException("Not supported stake value::3")

    def test_on_IRC31_Received(self):
        # GIVEN
        self.set_msg(self._owner)
        self.score.setMinimumStake(50 * EXA)
        _pool_address = create_address(AddressPrefix.CONTRACT)
        _pool_id = 1
        _user = self.test_account3
        self.score._poolStakeDetails[_user][_pool_id][Status.AVAILABLE] = 59 * EXA
        self.score._poolStakeDetails[_user][_pool_id][Status.STAKED] = 52 * EXA
        self.score._totalStaked[_pool_id] = 163 * EXA
        self.patch_internal_method(self.mock_dex, "balanceOf", lambda _a, _b: 111 * EXA)
        self.register_interface_score(self.mock_reward)
        self.score.addPool(_pool_address, _pool_id)
        # test
        _data = '{"method": "stake"}'.encode("utf-8")
        self.set_msg(self.mock_dex)
        self.score.onIRC31Received(_operator=self._owner, _from=_user, _id=_pool_id, _value=82 * EXA, _data=_data)

        # Validate
        self.assertEqual(29 * EXA, self.score._poolStakeDetails[_user][_pool_id][Status.AVAILABLE])
        self.assertEqual(82 * EXA, self.score._poolStakeDetails[_user][_pool_id][Status.STAKED])
        self.assertEqual((163 + 30) * EXA, self.score._totalStaked[_pool_id])

        self.assert_internal_call(self.mock_dex, "balanceOf", _user, _pool_id)
        self.assert_internal_call(self.mock_reward, "handleAction", _user, 52 * EXA, 163 * EXA, _pool_address)

    def test_unstake_validation(self):
        # GIVEN
        _user = self.test_account3
        self.set_msg(self._owner)
        self.score.setMinimumStake(50 * EXA)
        _pool_address = create_address(AddressPrefix.CONTRACT)
        _pool_id = 1
        self.score._poolStakeDetails[_user][_pool_id][Status.AVAILABLE] = 59 * EXA
        self.score._poolStakeDetails[_user][_pool_id][Status.STAKED] = 52 * EXA
        self.score._totalStaked[_pool_id] = 163 * EXA

        self.set_msg(_user)
        try:
            self.score.unstake(_pool_id, 10 * EXA)
        except IconScoreException as err:
            self.assertIn(f"{_pool_id} is not supported", str(err))
        else:
            raise IconScoreException("Unsupported pool")
        self.set_msg(self._owner)
        self.score.addPool(_pool_address, _pool_id)
        self.set_msg(_user)
        try:
            self.score.unstake(_pool_id, 53 * EXA)
        except IconScoreException as err:
            self.assertIn("Cannot unstake,user dont have enough staked balance", str(err))
        else:
            raise IconScoreException("Invalid unstake value")

        try:
            self.score.unstake(_pool_id, -1)
        except IconScoreException as err:
            self.assertIn("Cannot unstake less than zero", str(err))
        else:
            raise IconScoreException("Invalid unstake value")

    def test_unstake(self):
        # GIVEN
        self.set_msg(self._owner)
        _pool_address = create_address(AddressPrefix.CONTRACT)
        _pool_id = 1
        _user = self.test_account3
        self.score._poolStakeDetails[_user][_pool_id][Status.AVAILABLE] = 23 * EXA
        self.score._poolStakeDetails[_user][_pool_id][Status.STAKED] = 37 * EXA
        self.score._totalStaked[_pool_id] = 173 * EXA

        self.register_interface_score(self.mock_reward)
        self.register_interface_score(self.mock_dex)
        self.score.addPool(_pool_address, _pool_id)

        # test
        self.set_msg(_user)
        self.score.unstake(_pool_id, 29 * EXA)

        # Validate
        self.assertEqual(52 * EXA, self.score._poolStakeDetails[_user][_pool_id][Status.AVAILABLE])
        self.assertEqual(8 * EXA, self.score._poolStakeDetails[_user][_pool_id][Status.STAKED])
        self.assertEqual(144 * EXA, self.score._totalStaked[_pool_id])

        self.assert_internal_call(self.mock_dex, "transfer", _user, 29 * EXA, _pool_id, b'transferBackToUser')

        self.assert_internal_call(self.mock_reward, "handleAction", _user, 37 * EXA, 173 * EXA, _pool_address)
