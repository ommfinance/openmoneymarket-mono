from .rewardDistribution import *
from .utils.checks import *
from .utils.types import *

DAY_IN_MICROSECONDS = 86400 * 10 ** 6

TAG = 'Reward Distribution Controller'


class RewardDistributionController(RewardDistributionManager):
    USERS_UNCLAIMED_REWARDS = 'usersUnclaimedRewards'
    DAY = 'day'
    DIST_COMPLETE = 'distComplete'
    TOKEN_DIST_TRACKER = 'tokenDistTracker'
    IS_INITIALIZED = 'isInitialized'
    IS_REWARD_CLAIM_ENABLED = 'isRewardClaimEnabled'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._day = VarDB(self.DAY, db, value_type=int)
        self._isInitialized = VarDB(self.IS_INITIALIZED, db, value_type=bool)
        self._isRewardClaimEnabled = VarDB(self.IS_REWARD_CLAIM_ENABLED, db, value_type=bool)
        self._usersUnclaimedRewards = DictDB(self.USERS_UNCLAIMED_REWARDS, db, value_type=int, depth=2)
        self._tokenDistTracker = DictDB(self.TOKEN_DIST_TRACKER, db, value_type=int)

    def on_install(self, _addressProvider: Address, _startTimestamp: int,
                   _distPercentage: List[DistPercentage]) -> None:
        super().on_install(_addressProvider, _startTimestamp)

        self._rewardConfig.setRecipient("worker")
        self._rewardConfig.setRecipient("daoFund")
        self._rewardConfig.setRecipient("lendingBorrow")
        self._rewardConfig.setRecipient("liquidityProvider")
        self._updateDistPercentage(_distPercentage)
        self._isRewardClaimEnabled.set(False)

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=2)
    def Distribution(self, _recipient: str, _user: Address, _value: int):
        pass

    @eventlog(indexed=1)
    def State(self, _state: str):
        pass

    @eventlog
    def OmmTokenMinted(self, _day: int, _value: int):
        pass

    @eventlog
    def RewardsAccrued(self, _user: Address, _asset: Address, _rewards: int) -> None:
        pass

    @eventlog
    def RewardsClaimed(self, _user: Address, _rewards: int, _msg: str) -> None:
        pass

    @external(readonly=True)
    def name(self) -> str:
        return f"Omm {TAG}"

    @external(readonly=True)
    def getRecipients(self) -> list:
        return self._rewardConfig.getRecipients()

    @external
    def handleAction(self, _userAssetDetails: UserDetails) -> None:
        _asset = self.msg.sender
        self._handleAction(_asset, _userAssetDetails)

    @only_governance
    @external
    def disableRewardClaim(self):
        self._isRewardClaimEnabled.set(False)

    @only_governance
    @external
    def enableRewardClaim(self):
        self._isRewardClaimEnabled.set(True)

    @external(readonly=True)
    def isRewardClaimEnabled(self) -> bool:
        return self._isRewardClaimEnabled.get()

    @external
    @only_staked_lp
    def handleLPAction(self, _asset: Address, _userDetails: UserDetails) -> None:
        self._handleAction(_asset, _userDetails)

    def _handleAction(self, _asset: Address, _userDetails: UserDetails) -> None:
        _decimals = _userDetails.get("_decimals")

        _user = _userDetails.get("_user")
        _userBalance = convertToExa(_userDetails.get("_userBalance"), _decimals)
        _totalSupply = convertToExa(_userDetails.get("_totalSupply"), _decimals)

        RewardDistributionManager._require(self._rewardConfig.is_valid_asset(_asset), f'Asset Not Authorized: {_asset}')
        accruedRewards = self._updateUserReserveInternal(_user, _asset, _userBalance, _totalSupply)
        if accruedRewards != 0:
            self._usersUnclaimedRewards[_user][_asset] += accruedRewards
            self.RewardsAccrued(_user, _asset, accruedRewards)

    @external(readonly=True)
    def getDailyRewards(self, _day: int = None) -> dict:
        _day = self.getDay() if _day is None else _day
        _distribution = self.tokenDistributionPerDay(_day)
        _total_rewards = 0
        response = {}
        _assets = self._rewardConfig.getAssets()
        for _asset in _assets:
            _assetName = self._rewardConfig.getAssetName(_asset)
            _entity = self._rewardConfig.getEntity(_asset)
            _percentage = self._rewardConfig.getAssetPercentage(_asset)

            _entity_map = response.get(_entity, {})
            _entity_total = _entity_map.get("total", 0)

            _distribution_value = exaMul(_distribution, _percentage)
            _entity_map[_assetName] = _distribution_value
            _entity_map["total"] = _entity_total + _distribution_value

            response[_entity] = _entity_map
            _total_rewards += _distribution_value

        response["day"] = _day
        response['total'] = _total_rewards

        return response

    @external(readonly=True)
    def getRewards(self, _user: Address) -> dict:
        totalRewards = 0
        response = {}
        _assets = self._rewardConfig.getAssets()
        for _asset in _assets:
            _assetName = self._rewardConfig.getAssetName(_asset)
            _entity = self._rewardConfig.getEntity(_asset)

            entityDict = response.get(_entity, {})
            total = entityDict.get("total", 0)

            userAssetDetails = self._getUserAssetDetails(_asset, _user)
            unclaimedRewards = self._usersUnclaimedRewards[_user][_asset]
            unclaimedRewards += self._getUnclaimedRewards(_user, userAssetDetails)
            entityDict[_assetName] = unclaimedRewards
            total += unclaimedRewards
            entityDict["total"] = total
            response[_entity] = entityDict
            totalRewards += unclaimedRewards

        response['total'] = totalRewards
        response['now'] = self.now() // 10 ** 6

        return response

    @only_owner
    @external
    def startDistribution(self) -> None:
        if self.getDay() == 0 and not self._isInitialized.get():
            self._mintDailyOMM()
            self.updateEmissionPerSecond()
            self._isInitialized.set(True)

    @only_lending_pool
    @external
    def claimRewards(self, _user: Address) -> int:
        if not self.isRewardClaimEnabled():
            revert(f"{TAG} : Currently, the reward claim is not active")
        unclaimedRewards = 0
        accruedRewards = 0
        _assets = self._rewardConfig.getAssets()

        for _asset in _assets:
            _assetName = self._rewardConfig.getAssetName(_asset)
            unclaimedRewards += self._usersUnclaimedRewards[_user][_asset]
            userAssetDetails = self._getUserAssetDetails(_asset, _user)
            accruedRewards += self._updateUserReserveInternal(_user, userAssetDetails['asset'],
                                                              userAssetDetails['userBalance'],
                                                              userAssetDetails['totalBalance'])
            self._usersUnclaimedRewards[_user][_asset] = 0

        if accruedRewards != 0:
            unclaimedRewards += accruedRewards
            self.RewardsAccrued(_user, self.address, accruedRewards)

        if unclaimedRewards == 0:
            return 0

        ommToken = self.create_interface_score(self._addresses[OMM_TOKEN], TokenInterface)
        ommToken.transfer(_user, unclaimedRewards)

        self.RewardsClaimed(_user, unclaimedRewards, 'Asset rewards')

    @external
    def distribute(self) -> None:
        worker = self.create_interface_score(self._addresses[WORKER_TOKEN], WorkerTokenInterface)
        ommToken = self.create_interface_score(self._addresses[OMM_TOKEN], TokenInterface)
        day: int = self._day.get()

        if day >= self.getDay():
            return

        totalSupply = worker.totalSupply()
        tokenDistTracker = self._tokenDistTracker['worker']
        for user in worker.getWallets():
            if tokenDistTracker <= 0:
                break
            tokenAmount = exaMul(exaDiv(worker.balanceOf(user), totalSupply), tokenDistTracker)
            self.Distribution("worker", user, tokenAmount)
            ommToken.transfer(user, tokenAmount)
            totalSupply -= worker.balanceOf(user)
            tokenDistTracker -= tokenAmount

        daoFundAddress = self._addresses[DAO_FUND]
        tokenDistTrackerDaoFund: int = self._tokenDistTracker['daoFund']
        ommToken.transfer(daoFundAddress, tokenDistTrackerDaoFund)
        self.Distribution("daoFund", daoFundAddress, tokenDistTrackerDaoFund)
        self._day.set(day + 1)
        self._mintDailyOMM()

    @external(readonly=True)
    def getDistributedDay(self) -> int:
        return self._day.get()

    def _mintDailyOMM(self) -> None:
        day: int = self._day.get()
        tokenDistributionPerDay: int = self.tokenDistributionPerDay(day)
        ommToken = self.create_interface_score(self._addresses[OMM_TOKEN], TokenInterface)
        ommToken.mint(tokenDistributionPerDay)

        for recipient in ('worker', 'daoFund'):
            _distributionPercentage = self.getDistributionPercentage(recipient)
            self._tokenDistTracker[recipient] = exaMul(tokenDistributionPerDay, _distributionPercentage)
        self.OmmTokenMinted(day, tokenDistributionPerDay)

    @only_governance
    @external()
    def transferOmmToDaoFund(self, _value: int):
        ommToken = self.create_interface_score(self._addresses[OMM_TOKEN], TokenInterface)
        ommToken.transfer(self._addresses[DAO_FUND], _value)

    @external
    def tokenFallback(self, _from: Address, _value: int, _data: bytes) -> None:
        pass
