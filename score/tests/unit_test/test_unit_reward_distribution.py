import os
from unittest import mock
from unittest.mock import Mock, call

from iconservice import Address, IconScoreException, AddressPrefix
from tbears.libs.scoretest.patch.score_patcher import ScorePatcher, get_interface_score
from typing_extensions import TypedDict

from rewardDistribution.Math import exaDiv, exaMul
from rewardDistribution.rewardDistribution import AssetConfig
from rewardDistribution.rewardDistributionController import RewardDistributionController
from tbears.libs.scoretest.score_test_case import ScoreTestCase

EXA = 10 ** 18
TIME = 10 ** 6


def create_address(prefix: AddressPrefix = AddressPrefix.EOA) -> 'Address':
    return Address.from_bytes(prefix.to_bytes(1, 'big') + os.urandom(20))


ASSET_ADDRESS_1 = create_address(AddressPrefix.CONTRACT)
ASSET_ADDRESS_2 = create_address(AddressPrefix.CONTRACT)

REWARD_CONFIG_1 = {
    "asset": ASSET_ADDRESS_1,
    "assetName": "assetName_1",
    "_address": ASSET_ADDRESS_1,
    "distPercentage": 11 * EXA // 10,
    "totalSupply": 83 * EXA
}

REWARD_CONFIG_2 = {
    "asset": ASSET_ADDRESS_2,
    "assetName": "assetName_2",
    "distPercentage": 12 * EXA // 10,
    "_address": ASSET_ADDRESS_2,
    "totalSupply": 97 * EXA
}

DISTRIBUTION_CONFIG = {
    "worker": 10,
    "daoFund": 30
}


class DistributionPercentage(TypedDict):
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
        self.mock_lending_pool = Address.from_string(f"cx{'1212' * 10}")
        self.mock_omm_token = Address.from_string(f"cx{'1232' * 10}")
        self.mock_worker_token = Address.from_string(f"cx{'1233' * 10}")
        self.mock_lp_token = Address.from_string(f"cx{'1235' * 10}")
        self.mock_dao_fund = Address.from_string(f"cx{'1235' * 10}")

        self.set_tx(origin=self._owner)
        self.score.setAddresses([
            {"name": 'lendingPoolDataProvider', "address": self.mock_lending_pool_core},
            {"name": "ommToken", "address": self.mock_omm_token},
            {"name": "workerToken", "address": self.mock_worker_token},
            {"name": "lendingPool", "address": self.mock_lending_pool},
            {"name": "dex", "address": self.mock_lp_token},
            {"name": "daoFund", "address": self.mock_dao_fund}
        ])

        self.score._timestampAtStart.set(0)

        self.set_msg(self.test_account2, 1)

        self.test_account3 = create_address()
        self.test_account4 = create_address()
        account_info = {self.test_account3: 10 ** 21,
                        self.test_account4: 10 ** 21}
        ScoreTestCase.initialize_accounts(account_info)

    def _setup_asset_emission(self, account: Address, config):
        self.set_msg(account)
        self.patch_internal_method(config["asset"], "totalSupply", lambda: config["totalSupply"])

        self.score.configureAssetEmission([{
            "asset": config['asset'],
            "assetName": config['assetName'],
            "distPercentage": config['distPercentage'],
        }])
        self.set_msg(self.test_account2)

    def _setup_distribution_percentage(self, account: Address, config: DistributionPercentage):
        self.set_msg(account, 1)

        worker = config["worker"]
        dao_fund = config["daoFund"]

        self.score.setDailyDistributionPercentage("worker_token", worker)
        self.score.setDailyDistributionPercentage("daoFund", dao_fund)
        self.set_msg(self.test_account2, 1)

    def test_configure_asset_emission_not_owner(self):
        """
        configureAssetEmission : should throw SenderNotScoreOwnerError if caller is not owner while calling configureAssetEmission
        """
        try:
            self._setup_asset_emission(self.test_account2, REWARD_CONFIG_1)
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
            self._setup_asset_emission(self._owner, REWARD_CONFIG_1)
            _emissionPerSecond = exaMul(10 ** 24 // 86400, 11 * EXA // 10)

            self.assert_internal_call(REWARD_CONFIG_1['asset'], "totalSupply")
            self.score.AssetConfigUpdated.assert_called_with(ASSET_ADDRESS_1, _emissionPerSecond)

        _lastUpdateTimestamp = _mock_time_elapsed
        # time elapsed 31 day
        _mock_time_elapsed = 60 * 60 * 24 * 31 * TIME

        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self._setup_asset_emission(self._owner, REWARD_CONFIG_1)
            _new_asset_index = exaDiv(
                _emissionPerSecond * (_mock_time_elapsed - _lastUpdateTimestamp) // TIME,
                REWARD_CONFIG_1["totalSupply"]) + 0

            self.assertEqual(_new_asset_index, self.score._assetIndex[ASSET_ADDRESS_1])

            self.score.AssetIndexUpdated.assert_called_with(ASSET_ADDRESS_1, _new_asset_index)

            # emission after 31st day
            _emissionPerSecond = exaMul(4 * 10 ** 23 // 86400, 11 * EXA // 10)
            self.score.AssetConfigUpdated.assert_called_with(ASSET_ADDRESS_1, _emissionPerSecond)

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

        actual_result = self.score.getDailyDistributionPercentage("worker_token")
        self.assertEqual(DISTRIBUTION_CONFIG["worker"], actual_result)

        actual_result = self.score.getDailyDistributionPercentage("daoFund")
        self.assertEqual(DISTRIBUTION_CONFIG["daoFund"], actual_result)

    def test_handle_action_case(self):
        """
        test case https://docs.google.com/spreadsheets/d/149PP--2YLUHcq9_W4osZPHhuGDWHm1nnIb8tjF2C5u4/edit#gid=659147913
        """
        _asset_config = {
            "asset": ASSET_ADDRESS_1,
            "distPercentage": 15 * EXA // 10,
            "totalSupply": 0
        }

        _user1 = self.test_account3
        _user2 = self.test_account4

        _mock_time_elapsed = 0 * TIME
        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self._setup_asset_emission(self._owner, _asset_config)
        _last_updated_timestamp = _mock_time_elapsed

        _user2_balance = 0
        _total_supply = 0
        _current_index = 0
        _user1_balance = 0

        ## first deposit by user1
        ## user1 ==> deposit=>5,balance>5
        ## user2 ==> deposit=>0,balance=>0
        ## total_asset=>5
        ## time_elapse=>100
        _mock_time_elapsed = 100 * TIME

        self.assertEqual(0, self.score._userIndex[_user1][ASSET_ADDRESS_1])
        self.assertEqual(0, self.score._userIndex[_user2][ASSET_ADDRESS_1])
        self.assertEqual(0, self.score._assetIndex[ASSET_ADDRESS_1])

        _user = {
            "address": _user1,
            "balance": _user1_balance * EXA,
        }

        _asset = {
            "config": _asset_config,
            "balance": _total_supply * EXA
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }

        _current_index = self._call_handle_action(_user, _asset, _time, _current_index)

        _user1_balance += 5
        _total_supply += _user1_balance

        self.assertEqual(0, self.score._userIndex[_user1][ASSET_ADDRESS_1])
        self.assertEqual(0, self.score._userIndex[_user2][ASSET_ADDRESS_1])
        self.assertEqual(0, self.score._assetIndex[ASSET_ADDRESS_1])

        _last_updated_timestamp = _mock_time_elapsed  ##100
        ## first deposit by user2
        ## user1 ==> deposit=>5,balance=>5
        ## user2 ==> deposit=>10,balance=>0+10=10
        ## total_asset=>15
        ## time_elapse=>100+600=700
        _mock_time_elapsed = (100 + 600) * TIME
        _user = {
            "address": _user2,
            "balance": _user2_balance * EXA,
        }

        _asset = {
            "config": _asset_config,
            "balance": _total_supply * EXA
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }
        _current_index = self._call_handle_action(_user, _asset, _time, _current_index)

        _user2_balance += 10
        _total_supply += _user2_balance

        self.assertEqual(0, self.score._userIndex[_user1][ASSET_ADDRESS_1])
        self.assertAlmostEqual(2083.333333333330000000, self.score._userIndex[_user2][ASSET_ADDRESS_1] / EXA, 10)
        self.assertAlmostEqual(2083.333333333330000000, self.score._assetIndex[ASSET_ADDRESS_1] / EXA, 10)
        print(self.score._usersUnclaimedRewards[_user2])
        _last_updated_timestamp = _mock_time_elapsed  ##700

        ## 2nd deposit by user1
        ## user1 ==> deposit=>15,balance=>5+15=20
        ## user2 ==> deposit=>0,balance=>10
        ## total_asset=>30
        ## time_elapse=>700+600=1300
        _mock_time_elapsed = (700 + 600) * TIME
        _user = {
            "address": _user1,
            "balance": _user1_balance * EXA,
        }

        _asset = {
            "config": _asset_config,
            "balance": _total_supply * EXA
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }

        _current_index = self._call_handle_action(_user, _asset, _time, _current_index)

        _user1_balance += 15
        _total_supply += _user1_balance

        self.assertAlmostEqual(13888.888888888900000000,
                               self.score._usersUnclaimedRewards[_user1][ASSET_ADDRESS_1] / EXA, 10)
        self.assertAlmostEqual(2777.777777777770000000, self.score._userIndex[_user1][ASSET_ADDRESS_1] / EXA, 10)
        self.assertAlmostEqual(2083.333333333330000000, self.score._userIndex[_user2][ASSET_ADDRESS_1] / EXA, 10)
        self.assertAlmostEqual(2777.777777777770000000, self.score._assetIndex[ASSET_ADDRESS_1] / EXA, 10)

        _last_updated_timestamp = _mock_time_elapsed  ##1300

        ## 2nd deposit by user2
        ## user1 ==> deposit=>0,balance=>20
        ## user2 ==> deposit=>20,balance=>10+20=30
        ## total_asset=>50
        ## time_elapse=>1300+0=1300
        _mock_time_elapsed = 1300 * TIME

        _user = {
            "address": _user2,
            "balance": _user2_balance * EXA,
        }

        _asset = {
            "config": _asset_config,
            "balance": _total_supply * EXA
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }
        _current_index = self._call_handle_action(_user, _asset, _time, _current_index)

        _user2_balance += 20
        _total_supply += _user2_balance

        self.assertAlmostEqual(13888.8888888889, self.score._usersUnclaimedRewards[_user1][ASSET_ADDRESS_1] / EXA, 10)
        self.assertAlmostEqual(6944.4444444444, self.score._usersUnclaimedRewards[_user2][ASSET_ADDRESS_1] / EXA, 10)

        self.assertAlmostEqual(2777.7777777778, self.score._userIndex[_user1][ASSET_ADDRESS_1] / EXA, 10)
        self.assertAlmostEqual(2777.7777777778, self.score._userIndex[_user2][ASSET_ADDRESS_1] / EXA, 10)
        self.assertAlmostEqual(2777.7777777778, self.score._assetIndex[ASSET_ADDRESS_1] / EXA, 10)

        _last_updated_timestamp = _mock_time_elapsed  ##700

    def _call_handle_action(self, _user, _asset, _time, _old_index):
        _asset_address = _asset["config"]["asset"]
        _percentage = _asset["config"]["distPercentage"]
        _total_supply = _asset["balance"]

        _mock_time_elapsed = _time["mock_time_elapsed"]
        _last_timestamp = _time["last_timestamp"]

        _user_address = _user["address"]
        _user_balance = _user["balance"]
        _emission_per_second = exaMul(10 ** 24 // 86400, _percentage)
        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self.set_msg(_asset_address, 1)
            _user_old_index = self.score._userIndex[_user_address][_asset_address]
            _user_old_reward = self.score._usersUnclaimedRewards[_user_address]
            self.score.handleAction(_user_address, _user_balance, _total_supply)

            _time_delta = (_mock_time_elapsed - _last_timestamp) // TIME

            _current_index = (exaDiv(_emission_per_second * _time_delta,
                                     _total_supply) + _old_index) if _total_supply else 0

            _user_reward = (_current_index - _user_old_index) * _user_balance // EXA
            if _old_index != _current_index:
                self.score.AssetIndexUpdated.assert_called_with(_asset_address, _current_index)
                self.score.UserIndexUpdated.assert_called_with(_user_address, _asset_address, _current_index)

            if _user_reward != 0:
                self.score.RewardsAccrued.assert_called_with(_user_address, _asset_address, _user_reward)

            return _current_index

    def test_get_rewards_balance_0(self):
        """
        Should return 0 as reward balance if asset emission is not configureAssetEmission
        """
        self.register_interface_score(self.mock_lending_pool_core)

        actual_result = self.score.getRewards(self.test_account2)
        expected_result = {'totalRewards': 0}

        self.assertDictEqual(expected_result, actual_result)

    def test_get_rewards_balance_1(self):
        """
        getRewardBalance
        https://docs.google.com/spreadsheets/d/16XWl9FSGH7cVuUPAV7Ol0m-IdC441CMHqLVW-KJfiWQ/edit?usp=sharing
        Should return reward balance - case 1
        """

        _mock_time_elapsed = 0 * TIME
        _config = REWARD_CONFIG_1;
        _config["totalSupply"] = 0
        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self._setup_asset_emission(self._owner, REWARD_CONFIG_1)
        _last_updated_timestamp = _mock_time_elapsed

        _mock_time_elapsed = 400 * TIME
        _user_1 = self.test_account2
        _user_2 = self.test_account3
        _user1_balance = 0
        _user2_balance = 0
        _total_supply = 0
        ## given
        _user_1_rewards = {
            "worker": 10 * EXA,
            "daoFund": 40 * EXA,
        }
        _user_2_rewards = {
            "worker": 2 * 10 * EXA,
            "daoFund": 2 * 40 * EXA,
        }
        self.score._tokenValue = {
            _user_1: _user_1_rewards,
            _user_2: _user_2_rewards
        }
        _user = {
            "address": self.test_account2,
            "balance": _user1_balance * EXA,
        }
        _asset = {
            "config": REWARD_CONFIG_1,
            "balance": _total_supply * EXA
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }
        _current_index = self._call_handle_action(_user, _asset, _time, 0)
        _user1_balance += 100
        _total_supply += _user1_balance
        _last_updated_timestamp = _mock_time_elapsed
        self.patch_internal_method(self.mock_omm_token, "getPrincipalSupply",
                                   lambda _address: {
                                       'principalUserBalance': 0,
                                       'principalTotalSupply': 0
                                   })
        _supply = {
            'principalUserBalance': _user1_balance * EXA,
            'principalTotalSupply': _total_supply * EXA
        }
        self.patch_internal_method(ASSET_ADDRESS_1, "getPrincipalSupply",
                                   lambda _address: _supply)

        _mock_time_elapsed = 600 * TIME
        actual_result = self._call_get_rewards_balance(self.test_account2, _mock_time_elapsed, _supply)

        self.assertAlmostEqual(2546.2962962963, actual_result["assetName_1"] / EXA, 10)
        self.assertAlmostEqual(2546.2962962963, actual_result["totalRewards"] / EXA, 10)

        _mock_time_elapsed = 850 * TIME
        _user = {
            "address": _user_2,
            "balance": _user2_balance * EXA,
        }
        _asset = {
            "config": REWARD_CONFIG_1,
            "balance": _total_supply * EXA
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }

        _current_index = self._call_handle_action(_user, _asset, _time, _current_index)
        _user2_balance += 200
        _total_supply += _user2_balance
        _last_updated_timestamp = _mock_time_elapsed

        _mock_time_elapsed = 1300 * TIME
        _supply = {
            'principalUserBalance': _user1_balance * EXA,
            'principalTotalSupply': _total_supply * EXA
        }
        self.patch_internal_method(ASSET_ADDRESS_1, "getPrincipalSupply",
                                   lambda _address: _supply)

        actual_result = self._call_get_rewards_balance(_user_1, _mock_time_elapsed, _supply)
        self.assertAlmostEqual(7638.8888888889, actual_result["assetName_1"] / EXA, 10)
        self.assertAlmostEqual(7638.8888888889, actual_result["totalRewards"] / EXA, 10)

        _supply = {
            'principalUserBalance': _user2_balance * EXA,
            'principalTotalSupply': _total_supply * EXA
        }

        self.patch_internal_method(ASSET_ADDRESS_1, "getPrincipalSupply",
                                   lambda _address: _supply)

        actual_result = self._call_get_rewards_balance(_user_2, _mock_time_elapsed, _supply)
        self.assertAlmostEqual(3819.4444444445, actual_result["assetName_1"] / EXA, 9)
        self.assertAlmostEqual(3819.4444444445, actual_result["totalRewards"] / EXA, 9)

    def test_get_rewards_balance_2(self):
        """
        getRewardBalance
        https://docs.google.com/spreadsheets/d/16XWl9FSGH7cVuUPAV7Ol0m-IdC441CMHqLVW-KJfiWQ/edit?usp=sharing
        Should return reward balance - case 2
        """
        _user_1 = self.test_account2
        _user_2 = self.test_account3
        ## given

        _mock_time_elapsed = 0 * TIME
        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self._setup_asset_emission(self._owner, REWARD_CONFIG_1)
        _last_updated_timestamp = _mock_time_elapsed

        _mock_time_elapsed = 100 * TIME
        _user1_balance = 0
        _user2_balance = 0
        _total_supply = 0

        _user = {
            "address": _user_1,
            "balance": _user1_balance * EXA,
        }
        _asset = {
            "config": REWARD_CONFIG_1,
            "balance": _total_supply * EXA
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }
        _current_index = self._call_handle_action(_user, _asset, _time, 0)
        _user1_balance += 100
        _total_supply += _user1_balance
        _last_updated_timestamp = _mock_time_elapsed
        self.patch_internal_method(self.mock_omm_token, "getPrincipalSupply",
                                   lambda _address: {
                                       'principalUserBalance': 0,
                                       'principalTotalSupply': 0
                                   })
        _supply = {
            'principalUserBalance': _user1_balance * EXA,
            'principalTotalSupply': _total_supply * EXA
        }
        self.patch_internal_method(ASSET_ADDRESS_1, "getPrincipalSupply",
                                   lambda _address: _supply)

        _mock_time_elapsed = 500 * TIME
        actual_result = self._call_get_rewards_balance(_user_1, _mock_time_elapsed, _supply)
        self.assertAlmostEqual(5092.5925925926, actual_result["assetName_1"] / EXA, 9)
        self.assertAlmostEqual(5092.5925925926, actual_result["totalRewards"] / EXA, 9)

        _mock_time_elapsed = 500 * TIME
        _user = {
            "address": _user_2,
            "balance": _user2_balance * EXA,
        }
        _asset = {
            "config": REWARD_CONFIG_1,
            "balance": _total_supply * EXA
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }

        _current_index = self._call_handle_action(_user, _asset, _time, _current_index)
        _user2_balance += 100
        _total_supply += _user2_balance
        _last_updated_timestamp = _mock_time_elapsed

        ##withdraw
        _mock_time_elapsed = 800 * TIME
        _user = {
            "address": self.test_account2,
            "balance": _user1_balance * EXA,
        }
        _asset = {
            "config": REWARD_CONFIG_1,
            "balance": _total_supply * EXA
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }
        _current_index = self._call_handle_action(_user, _asset, _time, _current_index)

        self.assertAlmostEqual(7002.3148148148, self.score._usersUnclaimedRewards[self.test_account2][ASSET_ADDRESS_1]/EXA,9)

        _user1_balance -= 50
        _total_supply -= 50
        _last_updated_timestamp = _mock_time_elapsed

        _mock_time_elapsed = 1940 * TIME
        _supply = {
            'principalUserBalance': _user1_balance * EXA,
            'principalTotalSupply': _total_supply * EXA
        }
        self.patch_internal_method(ASSET_ADDRESS_1, "getPrincipalSupply",
                                   lambda _address: _supply)

        actual_result = self._call_get_rewards_balance(_user_1, _mock_time_elapsed, _supply)

        self.assertAlmostEqual(11840.2777777778, actual_result["assetName_1"] / EXA, 9)
        self.assertAlmostEqual(11840.2777777778, actual_result["totalRewards"] / EXA, 9)

        _supply = {
            'principalUserBalance': _user2_balance * EXA,
            'principalTotalSupply': _total_supply * EXA
        }
        self.patch_internal_method(ASSET_ADDRESS_1, "getPrincipalSupply",
                                   lambda _address: _supply)
        actual_result = self._call_get_rewards_balance(_user_2, _mock_time_elapsed, _supply)
        self.assertAlmostEqual(11585.6481481482, actual_result["assetName_1"] / EXA, 9)
        self.assertAlmostEqual(11585.6481481482, actual_result["totalRewards"] / EXA, 9)

    def _call_get_rewards_balance(self, _user, _mock_time_elapsed, _supply):
        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            actual_result = self.score.getRewards(_user)

            self.assert_internal_call(ASSET_ADDRESS_1, "getPrincipalSupply", _user)
            return actual_result

    def test_claim_rewards_case1(self):
        """
        claimRewards
        https://docs.google.com/spreadsheets/d/16XWl9FSGH7cVuUPAV7Ol0m-IdC441CMHqLVW-KJfiWQ/edit?usp=sharing
        Should able to claim reward - case 1
        """
        ## given

        _user1 = self.test_account2
        _user2 = self.test_account3

        self.patch_internal_method(self.mock_omm_token, "getPrincipalSupply",
                                   lambda _address: {
                                       'principalUserBalance': 0,
                                       'principalTotalSupply': 0
                                   })

        _mock_time_elapsed = 0 * TIME
        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self._setup_asset_emission(self._owner, REWARD_CONFIG_1)
        _last_updated_timestamp = _mock_time_elapsed

        _mock_time_elapsed = 100 * TIME
        _user1_balance = 0
        _user2_balance = 0
        _total_supply = 0

        _user = {
            "address": _user1,
            "balance": _user1_balance * EXA,
        }
        _asset = {
            "config": REWARD_CONFIG_1,
            "balance": _total_supply * EXA
        }
        _time = {
            "last_timestamp": _last_updated_timestamp,
            "mock_time_elapsed": _mock_time_elapsed
        }
        _current_index = self._call_handle_action(_user, _asset, _time, 0)
        _user1_balance += 100
        _total_supply += 100
        _last_updated_timestamp = _mock_time_elapsed
        _mock_time_elapsed = 500 * TIME
        _supply = {
            'principalUserBalance': _user1_balance * EXA,
            'principalTotalSupply': _total_supply * EXA
        }
        self.patch_internal_method(ASSET_ADDRESS_1, "getPrincipalSupply",
                                   lambda _address: _supply)

        actual_result = self._call_get_rewards_balance(_user1, _mock_time_elapsed, _supply)

        self.assertAlmostEqual(5092.5925925926, actual_result["assetName_1"] / EXA, 9)
        self.assertAlmostEqual(5092.5925925926, actual_result["totalRewards"] / EXA, 9)

        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self.set_msg(self.mock_lending_pool, 1)
            self.score.claimRewards(_user1)

            # _calls = [
            #     call(_user1,5092.5925925926, "Asset rewards")
            # ]
            #
            # self.score.RewardsClaimed.assert_has_calls(_calls)
            self.assert_internal_call(ASSET_ADDRESS_1, "getPrincipalSupply", _user1)

        self.assertEqual(0, self.score._usersUnclaimedRewards[_user1][ASSET_ADDRESS_1])
        self.assertEqual(self.score._userIndex[_user1][ASSET_ADDRESS_1], self.score._assetIndex[ASSET_ADDRESS_1])

        _mock_time_elapsed = 900 * TIME

        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self.set_msg(self.mock_lending_pool, 1)
            self.score.claimRewards(_user1)
            # TODO
            # self.score.RewardsClaimed.assert_called_with(_user1, 4000 * EXA, "borrowDepositRewards")
            self.assert_internal_call(ASSET_ADDRESS_1, "getPrincipalSupply", _user1)

        self.assertEqual(0, self.score._usersUnclaimedRewards[_user1][ASSET_ADDRESS_1])
        self.assertEqual(self.score._userIndex[_user1][ASSET_ADDRESS_1], self.score._assetIndex[ASSET_ADDRESS_1])

        _mock_time_elapsed = 1300 * TIME

        actual_result = self._call_get_rewards_balance(_user1, _mock_time_elapsed, _supply)
        self.assertAlmostEqual(5092.5925925926, actual_result["assetName_1"] / EXA, 9)
        self.assertAlmostEqual(5092.5925925926, actual_result["totalRewards"] / EXA, 9)

    def test_initial_distribute(self):

        self._setup_distribution_percentage(self._owner, DISTRIBUTION_CONFIG)

        self.register_interface_score(self.mock_worker_token)
        self.register_interface_score(self.mock_omm_token)

        ## initialized
        self.score._day.set(0)
        with mock.patch.object(self.score, "getDay", return_value=1):
            ## initialized and precompute ommICX
            self.patch_internal_method(self.mock_lp_token, "getTotalValue", lambda _name, _snapshot_id: 0 * EXA)

            self.score.distribute()

            self.assertEqual(0 * EXA, self.score._totalAmount["ommICX"])
            self.assertEqual(30 * 10 ** 6, self.score._tokenDistTracker["ommICX"])
            self.assertTrue(self.score._precompute["ommICX"])

            self.assert_internal_call(self.mock_lp_token, "getTotalValue", "OMM/sICX", 0)

            ##distribute ommICX skipped and precompute dex
            self.score.Distribution.reset_mock()
            self.patch_internal_method(self.mock_lp_token, "getTotalValue", lambda _name,
                                                                                   _snapshot_id: 0)

            self.score.distribute()

            self.assert_internal_call(self.mock_omm_token, "transfer", self.mock_dao_fund, 30 * 10 ** 6)
            self.score.Distribution.assert_called_with("daoFund", self.mock_dao_fund, 30 * 10 ** 6)

            self.assertTrue(self.score._distComplete["ommICX"])
            self.assertEqual(0, self.score._tokenDistTracker["ommICX"])

            self.assertEqual(0 * EXA, self.score._totalAmount["dex"])

            self.assertEqual(30 * 10 ** 6, self.score._tokenDistTracker["dex"])
            self.assertTrue(self.score._precompute["dex"])

            ##distribute dex skipped and distribute worker
            self.score.Distribution.reset_mock()
            _wallets = self._mock_worker_token_score()

            self.score.distribute()

            self.assert_internal_call(self.mock_omm_token, "transfer", self.mock_dao_fund, 30 * 10 ** 6)
            self.assertTrue(self.score._distComplete["dex"])
            self.assertEqual(0, self.score._tokenDistTracker["dex"])

            self.assertEqual(10 * 10 ** 5, self.score._tokenValue[_wallets[0]]["worker"])
            self.assertEqual(20 * 10 ** 5, self.score._tokenValue[_wallets[1]]["worker"])
            self.assertEqual(30 * 10 ** 5, self.score._tokenValue[_wallets[2]]["worker"])
            self.assertEqual(40 * 10 ** 5, self.score._tokenValue[_wallets[3]]["worker"])

            _calls = [
                call("daoFund", self.mock_dao_fund, 30 * 10 ** 6),
                call("worker", _wallets[0], 10 * 10 ** 5),
                call("worker", _wallets[1], 20 * 10 ** 5),
                call("worker", _wallets[2], 30 * 10 ** 5),
                call("worker", _wallets[3], 40 * 10 ** 5),
            ]
            self.score.Distribution.assert_has_calls(_calls)
            self.assertTrue(self.score._distComplete["dex"])

            ##distribute daoFund
            self.score.Distribution.reset_mock()

            self.score.distribute()
            self.assert_internal_call(self.mock_omm_token, "transfer", self.mock_dao_fund, 30 * 10 ** 6)
            self.assertTrue(self.score._distComplete["daoFund"])
            self.score.Distribution.assert_called_with("daoFund", self.mock_dao_fund, 30 * 10 ** 6)
            self.assertEqual(1, self.score._day.get())

    def test_distribute_worker(self):
        self._setup_distribution_percentage(self._owner, DISTRIBUTION_CONFIG)

        self.register_interface_score(self.mock_worker_token)
        self.register_interface_score(self.mock_omm_token)

        ## initialized
        self.score._day.set(31)
        self.score._initialize()
        self.score._precompute["dex"] = True
        self.score._precompute["ommICX"] = True
        self.score._distComplete["dex"] = True
        self.score._distComplete["ommICX"] = True

        with mock.patch.object(self.score, "getDay", return_value=32):
            _wallets = self._mock_worker_token_score()
            total_token = self.score._tokenDistTracker["worker"]
            self.score.distribute()

            mock_omm_token_score = get_interface_score(self.mock_omm_token)
            self.assertFalse(mock_omm_token_score.transfer.called);

            self.assertEqual(TestRewardDistributionController._calculate_amount(total_token, 10 * EXA, 100 * EXA),
                             self.score._tokenValue[_wallets[0]]["worker"])
            self.assertEqual(TestRewardDistributionController._calculate_amount(total_token, 20 * EXA, 100 * EXA),
                             self.score._tokenValue[_wallets[1]]["worker"])
            self.assertEqual(TestRewardDistributionController._calculate_amount(total_token, 30 * EXA, 100 * EXA),
                             self.score._tokenValue[_wallets[2]]["worker"])
            self.assertEqual(TestRewardDistributionController._calculate_amount(total_token, 40 * EXA, 100 * EXA),
                             self.score._tokenValue[_wallets[3]]["worker"])

            _calls = [
                call("worker", _wallets[0],
                     TestRewardDistributionController._calculate_amount(total_token, 10 * EXA, 100 * EXA)),
                call("worker", _wallets[1],
                     TestRewardDistributionController._calculate_amount(total_token, 20 * EXA, 100 * EXA)),
                call("worker", _wallets[2],
                     TestRewardDistributionController._calculate_amount(total_token, 30 * EXA, 100 * EXA)),
                call("worker", _wallets[3],
                     TestRewardDistributionController._calculate_amount(total_token, 40 * EXA, 100 * EXA)),
            ]
            self.score.Distribution.assert_has_calls(_calls)
            self.assertTrue(self.score._distComplete["worker"])

    def test_distribute_dao_fund(self):
        self._setup_distribution_percentage(self._owner, DISTRIBUTION_CONFIG)

        self.register_interface_score(self.mock_worker_token)
        self.register_interface_score(self.mock_omm_token)

        ## initialized
        self.score._day.set(31)
        self.score._initialize()
        self.score._precompute["dex"] = True
        self.score._precompute["ommICX"] = True
        self.score._distComplete["dex"] = True
        self.score._distComplete["ommICX"] = True
        self.score._distComplete["worker"] = True

        with mock.patch.object(self.score, "getDay", return_value=32):
            total_token = self.score._tokenDistTracker["daoFund"]
            self.score.distribute()

            self.assert_internal_call(self.mock_omm_token, "transfer", self.mock_dao_fund, total_token)
            self.assertTrue(self.score._distComplete["daoFund"])
            self.score.Distribution.assert_called_with("daoFund", self.mock_dao_fund, total_token)
            self.assertEqual(32, self.score._day.get())

    @staticmethod
    def _calculate_amount(total_token, user_balance, total_balance):
        return exaMul(total_token, exaDiv(user_balance, total_balance))

    def _mock_worker_token_score(self):
        _user1 = create_address()
        _user2 = create_address()
        _user3 = create_address()
        _user4 = create_address()
        _wallets = [
            _user1, _user2, _user3, _user4
        ]
        _balance = {
            f"{str(_user1)}": 10 * EXA,
            f"{str(_user2)}": 20 * EXA,
            f"{str(_user3)}": 30 * EXA,
            f"{str(_user4)}": 40 * EXA,
        }

        def side_effect(_user):
            return _balance.get(str(_user))

        self.register_interface_score(self.mock_worker_token)
        ScorePatcher.patch_internal_method(self.mock_worker_token, "totalSupply", lambda: 100 * EXA)
        ScorePatcher.patch_internal_method(self.mock_worker_token, "balanceOf", side_effect)
        ScorePatcher.patch_internal_method(self.mock_worker_token, "getWallets", lambda: _wallets)
        return _wallets;
