import os
from unittest import mock

from iconservice import Address, IconScoreException, AddressPrefix
from typing_extensions import TypedDict

from rewardDistribution.Math import exaDiv, exaMul
from rewardDistribution.rewardDistribution import AssetConfig
from rewardDistribution.rewardDistributionController import RewardDistributionController
from tbears.libs.scoretest.score_test_case import ScoreTestCase

EXA = 10 ** 18
TIME = 10 ** 6

ASSET_ADDRESS = Address.from_string(f"cx{'9841' * 10}")

ASSET_CONFIG = {
    "asset": ASSET_ADDRESS,
    "emissionPerSecond": 10 * EXA,
    "totalBalance": 0
}

DISTRIBUTION_CONFIG = {
    "ommICX": 30,
    "dex": 30,
    "worker": 10,
    "daoFund": 30
}


class DistributionPercentage(TypedDict):
    ommICX: int
    dex: int
    worker: int
    daoFund: int


def create_address(prefix: AddressPrefix = AddressPrefix.EOA) -> 'Address':
    return Address.from_bytes(prefix.to_bytes(1, 'big') + os.urandom(20))


class TestRewardDistributionController(ScoreTestCase):

    def setUp(self):
        super().setUp()
        self._owner = self.test_account1
        self.score = self.get_score_instance(RewardDistributionController, self._owner)
        self.mock_lending_pool_core = Address.from_string(f"cx{'1231' * 10}")
        self.mock_omm_token = Address.from_string(f"cx{'1232' * 10}")
        self.mock_worker_token = Address.from_string(f"cx{'1233' * 10}")
        self.mock_lp_token = Address.from_string(f"cx{'1235' * 10}")
        self.mock_dao_fun = Address.from_string(f"cx{'1235' * 10}")

        self.set_msg(self._owner, 1)
        self.score.setLendingPoolDataProvider(self.mock_lending_pool_core)
        self.score.setOmm(self.mock_omm_token)
        self.score.setWorkerToken(self.mock_worker_token)
        self.score.setLpToken(self.mock_lp_token)
        self.score.setDaoFund(self.mock_dao_fun)
        self.set_msg(self.test_account2, 1)

        self.test_account3 = create_address()
        self.test_account4 = create_address()
        account_info = {self.test_account3: 10 ** 21,
                        self.test_account4: 10 ** 21}
        ScoreTestCase.initialize_accounts(account_info)

    def _setup_asset_emission(self, account: Address, config: AssetConfig):
        self.set_msg(account, 1)
        self.score.configureAssetEmission([config])
        self.set_msg(self.test_account2, 1)

    def _setup_distribution_percentage(self, account: Address, config: DistributionPercentage):
        self.set_msg(account, 1)

        omm_icx = config["ommICX"]
        dex = config["dex"]
        worker = config["worker"]
        dao_fund = config["daoFund"]

        self.score.setDistPercentage(_ommICX=omm_icx, _dex=dex, _worker=worker, _daoFund=dao_fund)
        self.set_msg(self.test_account2, 1)

    def test_configure_asset_emission_not_owner(self):
        """
        configureAssetEmission : should throw SenderNotScoreOwnerError if caller is not owner while calling configureAssetEmission
        """
        try:

            self._setup_asset_emission(self.test_account2, ASSET_CONFIG)
        except IconScoreException as err:
            self.assertIn("SenderNotScoreOwnerError", str(err))
        else:
            raise IconScoreException("Unauthorized method call")

    def test_configure_asset_emission(self):
        """
        configureAssetEmission : should able to call configureAssetEmission if caller is owner
        """
        _mock_time_elapsed = 20 * TIME
        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self._setup_asset_emission(self._owner, ASSET_CONFIG)
            self.score.AssetConfigUpdated.assert_called_with(ASSET_ADDRESS, ASSET_CONFIG["emissionPerSecond"])

        _lastUpdateTimestamp = _mock_time_elapsed
        _mock_time_elapsed = 40 * TIME

        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self._setup_asset_emission(self._owner, ASSET_CONFIG)

            _new_asset_index = exaDiv(
                ASSET_CONFIG['emissionPerSecond'] * (_mock_time_elapsed - _lastUpdateTimestamp) // TIME,
                ASSET_CONFIG["totalBalance"]) + 0

            self.assertEqual(_new_asset_index, self.score._assetIndex[ASSET_ADDRESS])

            self.score.AssetConfigUpdated.assert_called_with(ASSET_ADDRESS, ASSET_CONFIG["emissionPerSecond"])
            self.score.AssetIndexUpdated.assert_called_with(ASSET_ADDRESS, _new_asset_index)

    def test_set_distribution_percentage_not_owner(self):
        """
        setDistPercentage : should throw SenderNotScoreOwnerError if caller is not owner while calling setDistPercentage
        """
        try:

            self._setup_distribution_percentage(self.test_account2, DISTRIBUTION_CONFIG)
        except IconScoreException as err:
            self.assertIn("SenderNotScoreOwnerError", str(err))
        else:
            raise IconScoreException("Unauthorized method call")

    def test_set_distribution_percentage(self):
        """
        setDistPercentage : should able to call setDistPercentage if caller is owner
        """

        self._setup_distribution_percentage(self._owner, DISTRIBUTION_CONFIG)

        actual_result = self.score.getDistPercentage()
        self.assertDictEqual(DISTRIBUTION_CONFIG, actual_result)

    def test_handle_action(self):
        """
        Should able call handleAction and update all indexes
        """

        _mock_time_elapsed = 100 * TIME
        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self._setup_asset_emission(self._owner, ASSET_CONFIG)
        _last_timestamp = _mock_time_elapsed

        _user = {
            "address": self.test_account2,
            "balance": 100 * EXA,
        }
        _asset = {
            "config": ASSET_CONFIG,
            "balance": 100 * EXA
        }
        _time = {
            "last_timestamp": _last_timestamp,
            "mock_time_elapsed": 200 * TIME
        }

        _current_index = self._call_handle_action(_user, _asset, _time, 0)

        _user = {
            "address": self.test_account3,
            "balance": 200 * EXA,
        }
        _asset = {
            "config": ASSET_CONFIG,
            "balance": 300 * EXA
        }
        _time = {
            "last_timestamp": _time["mock_time_elapsed"],
            "mock_time_elapsed": 500 * TIME
        }

        _current_index = self._call_handle_action(_user, _asset, _time, _current_index)

    def test_handle_action_case(self):
        """
        test case https://docs.google.com/spreadsheets/d/149PP--2YLUHcq9_W4osZPHhuGDWHm1nnIb8tjF2C5u4/edit#gid=659147913
        """
        _asset_config = {
            "asset": ASSET_ADDRESS,
            "emissionPerSecond": 10 * EXA,
            "totalBalance": 0
        }

        _user1 = self.test_account3
        _user2 = self.test_account4

        _mock_time_elapsed = 0 * TIME
        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self._setup_asset_emission(self._owner, _asset_config)
        _last_updated_timestamp = _mock_time_elapsed

        ## first deposit by user1
        ## user1 ==> deposit=>5,balance>5
        ## user2 ==> deposit=>0,balance=>0
        ## total_asset=>5
        ## time_elapse=>100
        _mock_time_elapsed = 100 * TIME
        _total_supply = 5 * EXA
        _current_index = 0
        _user = {
            "address": _user1,
            "balance": 5 * EXA,
        }

        _asset = {
            "config": _asset_config,
            "balance": _total_supply
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }
        # TODO
        self.assertEqual(0, self.score._userIndex[_user1][ASSET_ADDRESS])
        self.assertEqual(0, self.score._userIndex[_user2][ASSET_ADDRESS])
        self.assertEqual(0, self.score._assetIndex[ASSET_ADDRESS])

        _current_index = self._call_handle_action(_user, _asset, _time, _current_index)
        # TODO
        self.assertEqual(600, self.score._userIndex[_user1][ASSET_ADDRESS])
        self.assertEqual(0, self.score._userIndex[_user2][ASSET_ADDRESS])
        self.assertEqual(600, self.score._assetIndex[ASSET_ADDRESS])

        _last_updated_timestamp = _mock_time_elapsed  ##100
        ## first deposit by user2
        ## user1 ==> deposit=>5,balance=>5
        ## user2 ==> deposit=>10,balance=>0+10=10
        ## total_asset=>15
        ## time_elapse=>100+600=700
        _mock_time_elapsed = (100 + 600) * TIME
        _total_supply = (5 + 10) * EXA
        _user = {
            "address": _user2,
            "balance": 10 * EXA,
        }

        _asset = {
            "config": _asset_config,
            "balance": _total_supply
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }
        # TODO
        self.assertEqual(0, self.score._userIndex[_user1][ASSET_ADDRESS])
        self.assertEqual(0, self.score._userIndex[_user2][ASSET_ADDRESS])
        self.assertEqual(0, self.score._assetIndex[ASSET_ADDRESS])

        _current_index = self._call_handle_action(_user, _asset, _time, _current_index)

        # TODO
        self.assertEqual(1200, self.score._userIndex[_user1][ASSET_ADDRESS])
        self.assertEqual(1200, self.score._userIndex[_user2][ASSET_ADDRESS])
        self.assertEqual(1200, self.score._assetIndex[ASSET_ADDRESS])

        _last_updated_timestamp = _mock_time_elapsed  ##700

        ## 2nd deposit by user1
        ## user1 ==> deposit=>15,balance=>5+15=20
        ## user2 ==> deposit=>0,balance=>10
        ## total_asset=>30
        ## time_elapse=>700+600=1300
        _mock_time_elapsed = (700 + 600) * TIME
        _total_supply = (15 + 15) * EXA
        _user = {
            "address": _user1,
            "balance": (5 + 15) * EXA,
        }

        _asset = {
            "config": _asset_config,
            "balance": _total_supply
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }

        # TODO
        self.assertEqual(0, self.score._userIndex[_user1][ASSET_ADDRESS])
        self.assertEqual(0, self.score._userIndex[_user2][ASSET_ADDRESS])
        self.assertEqual(0, self.score._assetIndex[ASSET_ADDRESS])

        _current_index = self._call_handle_action(_user, _asset, _time, _current_index)

        # TODO
        self.assertEqual(8000, self.score._usersUnclaimedRewards[_user1])
        self.assertEqual(1200, self.score._userIndex[_user1][ASSET_ADDRESS])
        self.assertEqual(1200, self.score._userIndex[_user2][ASSET_ADDRESS])
        self.assertEqual(1200, self.score._assetIndex[ASSET_ADDRESS])

        _last_updated_timestamp = _mock_time_elapsed  ##1300

        ## 2nd deposit by user2
        ## user1 ==> deposit=>0,balance=>20
        ## user2 ==> deposit=>20,balance=>10+20=30
        ## total_asset=>50
        ## time_elapse=>1300+0=1300
        _mock_time_elapsed = (700 + 600) * TIME
        _total_supply = (30 + 20) * EXA
        _user = {
            "address": _user2,
            "balance": (10 + 20) * EXA,
        }

        _asset = {
            "config": _asset_config,
            "balance": _total_supply
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }

        # TODO
        self.assertEqual(0, self.score._userIndex[_user1][ASSET_ADDRESS])
        self.assertEqual(0, self.score._userIndex[_user2][ASSET_ADDRESS])
        self.assertEqual(0, self.score._assetIndex[ASSET_ADDRESS])

        _current_index = self._call_handle_action(_user, _asset, _time, _current_index)

        # TODO
        self.assertEqual(8000, self.score._usersUnclaimedRewards[_user1])
        self.assertEqual(1200, self.score._userIndex[_user1][ASSET_ADDRESS])
        self.assertEqual(1200, self.score._userIndex[_user2][ASSET_ADDRESS])
        self.assertEqual(1200, self.score._assetIndex[ASSET_ADDRESS])

        _last_updated_timestamp = _mock_time_elapsed  ##700

    def _call_handle_action(self, _user, _asset, _time, _current_index):
        _asset_address = _asset["config"]["asset"]
        _emission_per_second = _asset["config"]["emissionPerSecond"]
        _total_supply = _asset["balance"]

        _mock_time_elapsed = _time["mock_time_elapsed"]
        _last_timestamp = _time["last_timestamp"]

        _user_address = _user["address"]
        _user_balance = _user["balance"]

        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self.set_msg(_asset_address, 1)
            _user_old_index = self.score._userIndex[_user_address][_asset_address]
            _user_old_reward = self.score._usersUnclaimedRewards[_user_address]
            self.score.handleAction(_user_address, _user_balance, _total_supply)

            _time_delta = (_mock_time_elapsed - _last_timestamp) // TIME
            _current_index = exaDiv(_emission_per_second * _time_delta,
                                    _total_supply) + _current_index

            _user_reward = (_current_index - _user_old_index) * _user_balance // EXA

            self.score.AssetIndexUpdated.assert_called_with(_asset_address, _current_index)
            self.score.UserIndexUpdated.assert_called_with(_user_address, _asset_address, _current_index)
            self.score.RewardsAccrued.assert_called_with(_user_address, _user_reward)

            self.assertEqual(_user_reward + _user_old_reward, self.score._usersUnclaimedRewards[_user_address])
            self.assertEqual(_current_index, self.score._userIndex[_user_address][_asset_address])
            self.assertEqual(_current_index, self.score._assetIndex[_asset_address])

            return _current_index

    def test_get_rewards_balance_0(self):
        """
        Should return 0 as reward balance if asset emission is not configureAssetEmission
        """
        self.register_interface_score(self.mock_lending_pool_core)

        actual_result = self.score.getRewardsBalance(self.test_account2)
        expected_result = {'daoFund': 0,
                           'depositBorrowRewards': 0,
                           'dex': 0,
                           'liquidityRewards': 0,
                           'ommICX': 0,
                           'ommRewards': 0,
                           'total': 0,
                           'worker': 0}

        self.assertDictEqual(expected_result, actual_result)

    def test_get_rewards_balance_1(self):
        """
        Should return reward balance - case 1
        """

        _mock_time_elapsed = 0 * TIME
        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self._setup_asset_emission(self._owner, ASSET_CONFIG)
        _last_updated_timestamp = _mock_time_elapsed

        _mock_time_elapsed = 400 * TIME
        _user1_balance = 100
        _user = {
            "address": self.test_account2,
            "balance": _user1_balance * EXA,
        }
        _asset = {
            "config": ASSET_CONFIG,
            "balance": _user1_balance * EXA
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }

        _current_index = self._call_handle_action(_user, _asset, _time, 0)

        _last_updated_timestamp = _mock_time_elapsed

        _supply = {
            'principalUserBalance': _user1_balance * EXA,
            'principalTotalSupply': _user1_balance * EXA
        }
        self.patch_internal_method(self.mock_lending_pool_core, "getAssetPrincipalSupply",
                                   lambda asset, _address: _supply)

        _mock_time_elapsed = 600 * TIME
        self._call_get_rewards_balance(self.test_account2, _last_updated_timestamp, _mock_time_elapsed, _supply)

        _mock_time_elapsed = 900 * TIME
        _user2_balance = 200
        _user = {
            "address": self.test_account3,
            "balance": _user2_balance * EXA,
        }
        _asset = {
            "config": ASSET_CONFIG,
            "balance": (_user2_balance + _user1_balance) * EXA
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }

        _current_index = self._call_handle_action(_user, _asset, _time, _current_index)
        _last_updated_timestamp = _mock_time_elapsed

        _mock_time_elapsed = 1200 * TIME
        _supply = {
            'principalUserBalance': _user1_balance * EXA,
            'principalTotalSupply': (_user2_balance + _user1_balance) * EXA
        }
        self.patch_internal_method(self.mock_lending_pool_core, "getAssetPrincipalSupply",
                                   lambda asset, _address: _supply)

        self._call_get_rewards_balance(self.test_account2, _last_updated_timestamp, _mock_time_elapsed, _supply)

        _supply = {
            'principalUserBalance': _user2_balance * EXA,
            'principalTotalSupply': (_user2_balance + _user1_balance) * EXA
        }
        self.patch_internal_method(self.mock_lending_pool_core, "getAssetPrincipalSupply",
                                   lambda asset, _address: _supply)
        self._call_get_rewards_balance(self.test_account3, _last_updated_timestamp, _mock_time_elapsed, _supply)

    def _call_get_rewards_balance(self, _user, _last_updated_timestamp, _mock_time_elapsed, _supply):
        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            _unclaimed_rewards = self.score._usersUnclaimedRewards[_user]

            actual_result = self.score.getRewardsBalance(_user)
            _time_delta = (_mock_time_elapsed - _last_updated_timestamp) // TIME
            _temp_index = exaDiv(ASSET_CONFIG["emissionPerSecond"] * _time_delta,
                                 _supply['principalTotalSupply'])

            expected_result = {'worker': 0,
                               'ommICX': 0,
                               'dex': 0,
                               'daoFund': 0,
                               'depositBorrowRewards': _unclaimed_rewards + exaMul(_supply['principalUserBalance'],
                                                                                   _temp_index),
                               'ommRewards': 0,
                               'liquidityRewards': 0,
                               'total': 0}

            self.assert_internal_call(self.mock_lending_pool_core, "getAssetPrincipalSupply", ASSET_CONFIG["asset"],
                                      _user)
            self.assertDictEqual(expected_result, actual_result)

    def test_distribute(self):
        self.mock_worker_token_score()
        self.mock_lp_token_score()
        self.register_interface_score(self.mock_omm_token)

        self.score.distribute()

    def mock_worker_token_score(self):
        _wallets = [
            create_address(),
            create_address(),
            create_address(),
            create_address()
        ]
        self.patch_internal_method(self.mock_worker_token, "totalSupply", lambda: 100 * EXA)
        self.patch_internal_method(self.mock_worker_token, "balanceOf", lambda _user: 25 * EXA)
        self.patch_internal_method(self.mock_worker_token, "getWallets", lambda: _wallets)

    def mock_lp_token_score(self):
        self.patch_internal_method(self.mock_lp_token, "precompute", lambda _snapshot_id, batch_size: "_sanpshot_id")
        self.patch_internal_method(self.mock_lp_token, "getTotalValue", lambda _name, _snapshot_id: 1 * EXA)
        self.patch_internal_method(self.mock_lp_token, "getDataBatch", lambda _name, _snapshot_id, _limit, _offset: {})
