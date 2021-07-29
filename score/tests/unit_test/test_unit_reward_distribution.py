import os
from unittest import mock
from unittest.mock import call, ANY

from iconservice import Address, IconScoreException, AddressPrefix
from tbears.libs.scoretest.patch.score_patcher import ScorePatcher, get_interface_score
from tbears.libs.scoretest.score_test_case import ScoreTestCase
from typing_extensions import TypedDict

from rewardDistribution.Math import exaDiv, exaMul
from rewardDistribution.rewardDistributionController import RewardDistributionController

EXA = 10 ** 18
TIME = 10 ** 6


def create_address(prefix: AddressPrefix = AddressPrefix.EOA) -> 'Address':
    return Address.from_bytes(prefix.to_bytes(1, 'big') + os.urandom(20))


ASSET_ADDRESS_1 = create_address(AddressPrefix.CONTRACT)
ASSET_ADDRESS_2 = create_address(AddressPrefix.CONTRACT)

REWARD_CONFIG_1 = {
    "asset": ASSET_ADDRESS_1,
    "assetName": "assetName_1",
    "_id": -1,
    "rewardEntity": 'lendingBorrow',
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
    "worker": 30 * EXA // 100,
    "daoFund": 40 * EXA // 100,
    "lendingBorrow": 10 * EXA // 100,
    "liquidityProvider": 20 * EXA // 100
}


class DistributionPercentage(TypedDict):
    worker: int
    daoFund: int
    liquidityProvider: int
    lendingBorrow: int


def create_address(prefix: AddressPrefix = AddressPrefix.EOA) -> 'Address':
    return Address.from_bytes(prefix.to_bytes(1, 'big') + os.urandom(20))


class TestRewardDistributionController(ScoreTestCase):

    def setUp(self):
        super().setUp()
        self._owner = self.test_account1
        _params = [
            {"recipient": "worker", "percentage": DISTRIBUTION_CONFIG["worker"]},
            {"recipient": "daoFund", "percentage": DISTRIBUTION_CONFIG["daoFund"]},
            {"recipient": "liquidityProvider", "percentage": DISTRIBUTION_CONFIG["liquidityProvider"]},
            {"recipient": "lendingBorrow", "percentage": DISTRIBUTION_CONFIG["lendingBorrow"]},
        ]
        self.score = self.get_score_instance(RewardDistributionController, self._owner,
                                             on_install_params={"_distPercentage": _params})
        self.mock_lending_pool_core = Address.from_string(f"cx{'1231' * 10}")
        self.mock_lending_pool = Address.from_string(f"cx{'1212' * 10}")
        self.mock_omm_token = Address.from_string(f"cx{'1238' * 10}")
        self.mock_worker_token = Address.from_string(f"cx{'1233' * 10}")
        self.mock_lp_token = Address.from_string(f"cx{'1235' * 10}")
        self.mock_dao_fund = Address.from_string(f"cx{'1236' * 10}")
        self.mock_staked_lp = Address.from_string(f"cx{'1237' * 10}")

        self.set_tx(origin=self._owner)
        self.score.setAddresses([
            {"name": 'lendingPoolDataProvider', "address": self.mock_lending_pool_core},
            {"name": "ommToken", "address": self.mock_omm_token},
            {"name": "workerToken", "address": self.mock_worker_token},
            {"name": "lendingPool", "address": self.mock_lending_pool},
            {"name": "dex", "address": self.mock_lp_token},
            {"name": "stakedLP", "address": self.mock_staked_lp},
            {"name": "daoFund", "address": self.mock_dao_fund}
        ])

        self.score._timestampAtStart.set(0)

        self.set_msg(self.test_account2, 1)

        self.test_account3 = create_address()
        self.test_account4 = create_address()
        account_info = {self.test_account3: 10 ** 21,
                        self.test_account4: 10 ** 21}
        ScoreTestCase.initialize_accounts(account_info)

    def test_token_dist_per_day(self):
        """
        Inflation should rise by 3% every year
        """
        tokens_yr_5 = self.score.tokenDistributionPerDay(5*365)
        tokens_yr_6 = self.score.tokenDistributionPerDay(6*365)
        inflation_56 = (tokens_yr_6-tokens_yr_5)/tokens_yr_5
        self.assertEqual(0.03, inflation_56)
        tokens_yr_7 = self.score.tokenDistributionPerDay(7*365)
        inflation_67 = (tokens_yr_7-tokens_yr_6)/tokens_yr_6
        self.assertEqual(0.03, inflation_67)

    def _setup_asset_emission(self, account: Address, config):
        self.set_msg(account)
        self.patch_internal_method(config["asset"], "getTotalStaked", lambda: config["totalSupply"])

        self.score.configureAssets([{
            "asset": config['asset'],
            "_id": config['_id'],
            "rewardEntity": config['rewardEntity'],
            "assetName": config['assetName'],
            "distPercentage": config['distPercentage'],
        }])
        self.set_msg(self.test_account2)

    def _setup_distribution_percentage(self, account: Address, config: DistributionPercentage):
        self.set_msg(account, 1)

        _params = [
            {"recipient": "worker", "percentage": config["worker"]},
            {"recipient": "daoFund", "percentage": config["daoFund"]},
            {"recipient": "liquidityProvider", "percentage": config["liquidityProvider"]},
            {"recipient": "lendingBorrow", "percentage": config["lendingBorrow"]},
        ]
        self.score.setDistributionPercentage(_params)
        self.set_msg(self.test_account2, 1)

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

        actual_result = self.score.getDistributionPercentage("worker")
        self.assertEqual(DISTRIBUTION_CONFIG["worker"], actual_result)

        actual_result = self.score.getDistributionPercentage("daoFund")
        self.assertEqual(DISTRIBUTION_CONFIG["daoFund"], actual_result)

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
        self._setup_distribution_percentage(self._owner, DISTRIBUTION_CONFIG)
        _mock_time_elapsed = 20 * TIME
        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self._setup_asset_emission(self._owner, REWARD_CONFIG_1)
            _emissionPerSecond = exaMul(10 ** 24 // 86400, 10 * 11 * EXA // 1000)

            self.assert_internal_call(REWARD_CONFIG_1['asset'], "getTotalStaked")
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
            _emissionPerSecond = exaMul(4 * 10 ** 23 // 86400, 10 * 11 * EXA // 1000)
            self.score.AssetConfigUpdated.assert_called_with(ASSET_ADDRESS_1, _emissionPerSecond)

    def test_handle_action_case(self):
        """
        test case https://docs.google.com/spreadsheets/d/149PP--2YLUHcq9_W4osZPHhuGDWHm1nnIb8tjF2C5u4/edit#gid=659147913
        """
        _asset_config = {
            "asset": ASSET_ADDRESS_1,
            "assetName": "assetName_1",
            "_id": -1,
            "rewardEntity": 'lendingBorrow',
            "distPercentage": 15 * EXA // 10,
            "totalSupply": 0
        }
        self._setup_distribution_percentage(self._owner, DISTRIBUTION_CONFIG)

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
        self.assertAlmostEqual(208.3333333333, self.score._userIndex[_user2][ASSET_ADDRESS_1] / EXA, 9)
        self.assertAlmostEqual(208.3333333333, self.score._assetIndex[ASSET_ADDRESS_1] / EXA, 9)

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

        self.assertAlmostEqual(1388.8888888889,
                               self.score._usersUnclaimedRewards[_user1][ASSET_ADDRESS_1] / EXA, 9)
        self.assertAlmostEqual(277.7777777778, self.score._userIndex[_user1][ASSET_ADDRESS_1] / EXA, 9)
        self.assertAlmostEqual(208.3333333333, self.score._userIndex[_user2][ASSET_ADDRESS_1] / EXA, 9)
        self.assertAlmostEqual(277.7777777778, self.score._assetIndex[ASSET_ADDRESS_1] / EXA, 9)

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

        self.assertAlmostEqual(1388.8888888889, self.score._usersUnclaimedRewards[_user1][ASSET_ADDRESS_1] / EXA, 9)
        self.assertAlmostEqual(694.4444444444, self.score._usersUnclaimedRewards[_user2][ASSET_ADDRESS_1] / EXA, 9)

        self.assertAlmostEqual(277.7777777778, self.score._userIndex[_user1][ASSET_ADDRESS_1] / EXA, 9)
        self.assertAlmostEqual(277.7777777778, self.score._userIndex[_user2][ASSET_ADDRESS_1] / EXA, 9)
        self.assertAlmostEqual(277.7777777778, self.score._assetIndex[ASSET_ADDRESS_1] / EXA, 9)

        _last_updated_timestamp = _mock_time_elapsed  ##700

    def _call_handle_action(self, _user, _asset, _time, _old_index):
        _asset_address = _asset["config"]["asset"]
        _rewardEntity = _asset["config"]["rewardEntity"]
        _percentage = exaMul(_asset["config"]["distPercentage"], DISTRIBUTION_CONFIG[_rewardEntity])
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
        self.patch_internal_method(self.mock_omm_token, "getPrincipalSupply",
                                   lambda _address: {
                                       'principalUserBalance': 0,
                                       'principalTotalSupply': 0
                                   })
        actual_result = self.score.getRewards(self.test_account2)

        self.assertEqual(0, actual_result["total"])

    def test_get_rewards_balance_1(self):
        """
        getRewardBalance
        https://docs.google.com/spreadsheets/d/16XWl9FSGH7cVuUPAV7Ol0m-IdC441CMHqLVW-KJfiWQ/edit?usp=sharing
        Should return reward balance - case 1
        """

        _mock_time_elapsed = 0 * TIME
        _config = REWARD_CONFIG_1;
        _config["totalSupply"] = 0
        self._setup_distribution_percentage(self._owner, DISTRIBUTION_CONFIG)

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

        self.assertAlmostEqual(254.6296296296, actual_result["reserve"]["assetName_1"] / EXA, 9)
        self.assertAlmostEqual(254.6296296296, actual_result["total"] / EXA, 9)

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
        self.assertAlmostEqual(763.8888888889, actual_result["reserve"]["assetName_1"] / EXA, 9)
        self.assertAlmostEqual(763.8888888889, actual_result["total"] / EXA, 9)

        _supply = {
            'principalUserBalance': _user2_balance * EXA,
            'principalTotalSupply': _total_supply * EXA
        }

        self.patch_internal_method(ASSET_ADDRESS_1, "getPrincipalSupply",
                                   lambda _address: _supply)

        actual_result = self._call_get_rewards_balance(_user_2, _mock_time_elapsed, _supply)
        self.assertAlmostEqual(381.9444444444, actual_result["reserve"]["assetName_1"] / EXA, 9)
        self.assertAlmostEqual(381.9444444444, actual_result["total"] / EXA, 9)

    def test_get_rewards_balance_2(self):
        """
        getRewardBalance
        https://docs.google.com/spreadsheets/d/16XWl9FSGH7cVuUPAV7Ol0m-IdC441CMHqLVW-KJfiWQ/edit?usp=sharing
        Should return reward balance - case 2
        """
        _user_1 = self.test_account2
        _user_2 = self.test_account3
        ## given
        self._setup_distribution_percentage(self._owner, DISTRIBUTION_CONFIG)
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
        self.assertAlmostEqual(509.2592592593, actual_result["reserve"]["assetName_1"] / EXA, 9)
        self.assertAlmostEqual(509.2592592593, actual_result["total"] / EXA, 9)

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

        self.assertAlmostEqual(700.2314814815,
                               self.score._usersUnclaimedRewards[self.test_account2][ASSET_ADDRESS_1] / EXA, 9)

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

        self.assertAlmostEqual(1184.0277777778, actual_result["reserve"]["assetName_1"] / EXA, 9)
        self.assertAlmostEqual(1184.0277777778, actual_result["total"] / EXA, 9)

        _supply = {
            'principalUserBalance': _user2_balance * EXA,
            'principalTotalSupply': _total_supply * EXA
        }
        self.patch_internal_method(ASSET_ADDRESS_1, "getPrincipalSupply",
                                   lambda _address: _supply)
        actual_result = self._call_get_rewards_balance(_user_2, _mock_time_elapsed, _supply)
        self.assertAlmostEqual(1158.5648148148, actual_result["reserve"]["assetName_1"] / EXA, 9)
        self.assertAlmostEqual(1158.5648148148, actual_result["total"] / EXA, 9)

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
        self._setup_distribution_percentage(self._owner, DISTRIBUTION_CONFIG)
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

        self.assertAlmostEqual(509.2592592593, actual_result['reserve']["assetName_1"] / EXA, 9)
        self.assertAlmostEqual(509.2592592593, actual_result["total"] / EXA, 9)

        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self.set_msg(self.mock_lending_pool, 1)
            self.score.claimRewards(_user1)

            _calls = [
                call(_user1, ANY, "Asset rewards")
            ]

            self.score.RewardsClaimed.assert_has_calls(_calls)
            self.score.RewardsAccrued.assert_called_with(_user1, self.score.address, ANY)
            self.assert_internal_call(ASSET_ADDRESS_1, "getPrincipalSupply", _user1)
            self.assert_internal_call(self.mock_omm_token, "transfer", _user1, ANY)

        self.assertEqual(0, self.score._usersUnclaimedRewards[_user1][ASSET_ADDRESS_1])
        self.assertEqual(self.score._userIndex[_user1][ASSET_ADDRESS_1], self.score._assetIndex[ASSET_ADDRESS_1])

        _mock_time_elapsed = 999 * TIME

        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self.set_msg(self.mock_lending_pool, 1)
            self.score.claimRewards(_user1)
            self.score.RewardsClaimed.assert_called_with(_user1, ANY, "Asset rewards")
            self.score.RewardsAccrued.assert_called_with(_user1, self.score.address, ANY)
            self.assert_internal_call(ASSET_ADDRESS_1, "getPrincipalSupply", _user1)
            self.assert_internal_call(self.mock_omm_token, "transfer", _user1, ANY)

        self.assertEqual(0, self.score._usersUnclaimedRewards[_user1][ASSET_ADDRESS_1])
        self.assertEqual(self.score._userIndex[_user1][ASSET_ADDRESS_1], self.score._assetIndex[ASSET_ADDRESS_1])
        self.assertAlmostEqual(11.4456018519, self.score._assetIndex[ASSET_ADDRESS_1] / EXA, 9)

        _mock_time_elapsed = 1354 * TIME

        actual_result = self._call_get_rewards_balance(_user1, _mock_time_elapsed, _supply)
        self.assertAlmostEqual(451.9675925926, actual_result["reserve"]["assetName_1"] / EXA, 9)
        self.assertAlmostEqual(451.9675925926, actual_result["total"] / EXA, 9)

    def test_initial_distribute(self):

        self._setup_distribution_percentage(self._owner, DISTRIBUTION_CONFIG)

        self.register_interface_score(self.mock_worker_token)
        self.register_interface_score(self.mock_omm_token)

        ## initialized
        self.score._day.set(0)
        with mock.patch.object(self.score, "getDay", return_value=1):
            ##distribute dex skipped and distribute worker
            _wallets = self._mock_worker_token_score()

            self.score.distribute()
            _worker_token = DISTRIBUTION_CONFIG['worker']
            mock_omm_token_score = get_interface_score(self.mock_omm_token)
            _calls = [
                call(_wallets[0], exaMul(1 * 10 ** 6 * 10 ** 18, _worker_token)),
                call(_wallets[1], exaMul(2 * 10 ** 6 * 10 ** 18, _worker_token)),
                call(_wallets[2], exaMul(3 * 10 ** 6 * 10 ** 18, _worker_token)),
                call(_wallets[3], exaMul(4 * 10 ** 6 * 10 ** 18, _worker_token)),
            ]
            mock_omm_token_score.transfer.assert_has_calls(_calls)

            _calls = [
                call("worker", _wallets[0], exaMul(1 * 10 ** 6 * 10 ** 18, _worker_token)),
                call("worker", _wallets[1], exaMul(2 * 10 ** 6 * 10 ** 18, _worker_token)),
                call("worker", _wallets[2], exaMul(3 * 10 ** 6 * 10 ** 18, _worker_token)),
                call("worker", _wallets[3], exaMul(4 * 10 ** 6 * 10 ** 18, _worker_token)),
            ]
            self.score.Distribution.assert_has_calls(_calls)
            self.assertTrue(self.score._distComplete["worker"])

            ##distribute daoFund
            self.score.Distribution.reset_mock()
            _dao_fund_percentage = DISTRIBUTION_CONFIG['daoFund']
            self.score.distribute()
            self.assert_internal_call(self.mock_omm_token, "transfer", self.mock_dao_fund,
                                      exaMul(1 * 10 ** 6 * 10 ** 18, _dao_fund_percentage))
            self.assertTrue(self.score._distComplete["daoFund"])
            self.score.Distribution.assert_called_with("daoFund", self.mock_dao_fund,
                                                       exaMul(1 * 10 ** 6 * 10 ** 18, _dao_fund_percentage))
            self.assertEqual(1, self.score._day.get())

    def test_distribute_dao_fund(self):
        self._setup_distribution_percentage(self._owner, DISTRIBUTION_CONFIG)

        self.register_interface_score(self.mock_worker_token)
        self.register_interface_score(self.mock_omm_token)

        ## initialized
        self.score._day.set(31)
        self.score._initialize()
        self.score._distComplete["worker"] = True

        with mock.patch.object(self.score, "getDay", return_value=32):
            total_token = self.score._tokenDistTracker["daoFund"]
            self.score.distribute()

            self.assert_internal_call(self.mock_omm_token, "transfer", self.mock_dao_fund, total_token)
            self.assertTrue(self.score._distComplete["daoFund"])
            self.score.Distribution.assert_called_with("daoFund", self.mock_dao_fund, total_token)
            self.assertEqual(32, self.score._day.get())

    def test_all_dist_percentage(self):
        self._setup_distribution_percentage(self._owner, DISTRIBUTION_CONFIG)
        _mock_time_elapsed = 0
        reserve_config = {
            "asset": ASSET_ADDRESS_1,
            "assetName": "assetName_1",
            "_id": -1,
            "rewardEntity": 'lendingBorrow',
            "distPercentage": 19 * EXA // 100,
        }
        omm_config = {
            "asset": create_address(AddressPrefix.CONTRACT),
            "assetName": "OMM",
            "_id": -1,
            "rewardEntity": 'liquidityProvider',
            "distPercentage": 25 * EXA // 100,
        }
        lp_config = {
            "asset": create_address(AddressPrefix.CONTRACT),
            "assetName": "lpName",
            "_id": 17,
            "rewardEntity": 'liquidityProvider',
            "distPercentage": 33 * EXA // 100,
        }
        with mock.patch.object(self.score, "now", return_value=_mock_time_elapsed):
            self.patch_internal_method(reserve_config["asset"], "getTotalStaked", lambda: 0)
            self.set_msg(self._owner)
            self.score.configureAssets([{
                "asset": reserve_config['asset'],
                "_id": reserve_config['_id'],
                "rewardEntity": reserve_config['rewardEntity'],
                "assetName": reserve_config['assetName'],
                "distPercentage": reserve_config['distPercentage'],
            }])
            self.set_msg(self.mock_omm_token)
            self.patch_internal_method(omm_config["asset"], "getTotalStaked", lambda: 0)

            self.score.configureLPEmission([{
                "asset": omm_config['asset'],
                "_id": omm_config['_id'],
                "rewardEntity": omm_config['rewardEntity'],
                "assetName": omm_config['assetName'],
                "distPercentage": omm_config['distPercentage'],
            }])
            self.set_msg(self.mock_staked_lp)
            self.patch_internal_method(self.mock_staked_lp, "getTotalStaked", lambda _pool: 0)

            self.score.configureLPEmission([{
                "asset": lp_config['asset'],
                "_id": lp_config['_id'],
                "rewardEntity": lp_config['rewardEntity'],
                "assetName": lp_config['assetName'],
                "distPercentage": lp_config['distPercentage'],
            }])

        allPercentage = self.score.allAssetDistPercentage()

        self.assertEqual(10 * 19 * EXA // (100 * 100), allPercentage["reserve"]["assetName_1"])
        self.assertEqual(20 * 25 * EXA // (100 * 100), allPercentage["staking"]["OMM"])
        self.assertEqual(20 * 33 * EXA // (100 * 100), allPercentage["liquidity"]["lpName"])
        
        lpPercentage = self.score.distPercentageOfAllLP()
        self.assertDictEqual({"liquidity": {17: 20 * 33 * EXA // (100 * 100)}}, lpPercentage)

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
        return _wallets
