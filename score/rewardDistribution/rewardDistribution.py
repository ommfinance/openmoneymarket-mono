from .addresses import Addresses
from .utils.math import *
from .rewardConfigurationDB import RewardConfigurationDB
from .utils.checks import *
from .utils.types import *
from .interfaces import *

TAG = 'Omm Reward Distribution Manager'

DAY_IN_MICROSECONDS = 86400 * 10 ** 6
MINUTE_IN_MICROSECONDS = 60 * 10 ** 6


class RewardDistributionManager(Addresses):
    REWARD_CONFIG = 'rewardConfig'
    LAST_UPDATE_TIMESTAMP = 'lastUpdateTimestamp'
    TIMESTAMP_AT_START = 'timestampAtStart'
    ASSET_INDEX = 'assetIndex'
    USER_INDEX = 'userIndex'
    RESERVE_ASSETS = 'reserveAssets'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._rewardConfig = RewardConfigurationDB(self.REWARD_CONFIG, db)

        self._lastUpdateTimestamp = DictDB(self.LAST_UPDATE_TIMESTAMP, db, value_type=int)
        self._assetIndex = DictDB(self.ASSET_INDEX, db, value_type=int)
        self._userIndex = DictDB(self.USER_INDEX, db, value_type=int, depth=2)

        self._reserveAssets = ArrayDB(self.RESERVE_ASSETS, db, value_type=Address)
        self._timestampAtStart = VarDB(self.TIMESTAMP_AT_START, db, value_type=int)

    def on_install(self, _address: Address, _timestamp: int) -> None:
        super().on_install(_address)
        self._timestampAtStart.set(_timestamp)

    def on_update(self) -> None:
        super().on_update()

    @eventlog(indexed=1)
    def AssetIndexUpdated(self, _asset: Address, _oldIndex: int, _newIndex: int) -> None:
        pass

    @eventlog(indexed=2)
    def UserIndexUpdated(self, _user: Address, _asset: Address, _oldIndex: int, _newIndex: int) -> None:
        pass

    @eventlog(indexed=1)
    def AssetConfigUpdated(self, _asset: Address, _emissionPerSecond: int) -> None:
        pass

    @external(readonly=True)
    def getAssetEmission(self) -> dict:
        return self._rewardConfig.getAllEmissionPerSecond()

    @external(readonly=True)
    def getAssets(self) -> list:
        return [asset for asset in self._rewardConfig.getAssets()]

    @staticmethod
    def _require(_condition: bool, _message: str):
        if not _condition:
            revert(f'{TAG}:  {_message}')

    @external(readonly=True)
    def getAssetNames(self) -> dict:
        return self._rewardConfig.getAssetNames()

    @external(readonly=True)
    def getIndexes(self, _user: Address, _asset: Address) -> dict:
        return {
            'userIndex': self._userIndex[_user][_asset],
            'assetIndex': self._assetIndex[_asset]
        }

    @only_owner
    @external
    def setAssetName(self, _asset: Address, _name: str):
        self._rewardConfig.setAssetName(_asset, _name)

    def _updateDistPercentage(self, _distPercentage: List[DistPercentage]):
        if ((self.now() - self._timestampAtStart.get()) - self.getDay() * DAY_IN_MICROSECONDS) < 15 * MINUTE_IN_MICROSECONDS:
            revert(f"{TAG}: Distribution percentage to be changed within 15 minutes of the start of the day")

        totalPercentage = 0
        for config in _distPercentage:
            _recipient = config["recipient"]
            _percentage = config["percentage"]
            totalPercentage += _percentage
            self._rewardConfig.setDistributionPercentage(config["recipient"], config["percentage"])

        if totalPercentage != EXA:
            revert(f"{TAG}: Percentage doesn't sum upto 100")

    @only_owner
    @external
    def setDistributionPercentage(self, _distPercentage: List[DistPercentage]):
        self._updateDistPercentage(_distPercentage)
        self.updateEmissionPerSecond()

    @external(readonly=True)
    def getDistributionPercentage(self, _recipient: str) -> int:
        return self._rewardConfig.getDistributionPercentage(_recipient)

    @external(readonly=True)
    def getAllDistributionPercentage(self) -> dict:
        return self._rewardConfig.getAllDistributionPercentage()

    @external(readonly=True)
    def assetDistPercentage(self, asset: Address) -> int:
        return self._rewardConfig.getAssetPercentage(asset)

    @external(readonly=True)
    def allAssetDistPercentage(self) -> dict:
        return self._rewardConfig.getAssetConfigs()

    @external(readonly=True)
    def distPercentageOfAllLP(self) -> dict:
        return self._rewardConfig.assetConfigOfLiquidityProvider()

    def _configureAsset(self, distributionPerDay: int, _assetConfig: AssetConfig):
        asset = _assetConfig['asset']
        self._rewardConfig.setAssetConfig(_assetConfig)
        _totalBalance = self._getTotalBalance(asset)
        self._updateAssetStateInternal(asset, _totalBalance)
        _emissionPerSecond = self._rewardConfig.updateEmissionPerSecond(asset, distributionPerDay)
        self.AssetConfigUpdated(asset, _emissionPerSecond)

    @only_governance
    @external
    def configureAssetConfigs(self, _assetConfig: List[AssetConfig]) -> None:
        distributionPerDay = self.tokenDistributionPerDay(self.getDay())
        for config in _assetConfig:
            self._configureAsset(distributionPerDay, config)

    @only_governance
    @external
    def configureAssetConfig(self, _assetConfig: AssetConfig) -> None:
        distributionPerDay = self.tokenDistributionPerDay(self.getDay())
        self._configureAsset(distributionPerDay, _assetConfig)

    @only_governance
    @external
    def removeAssetConfig(self, _asset: Address) -> None:
        _totalBalance = self._getTotalBalance(_asset)
        self._updateAssetStateInternal(_asset, _totalBalance)

        self._rewardConfig.removeAssetConfig(_asset)

    @external(readonly=True)
    def getPoolIDByAsset(self, _asset: Address) -> int:
        return self._rewardConfig.getPoolID(_asset)

    @only_owner
    @external
    def updateEmissionPerSecond(self) -> None:
        distributionPerDay = self.tokenDistributionPerDay(self.getDay())
        _assets = self._rewardConfig.getAssets()
        for asset in _assets:
            _totalBalance = self._getTotalBalance(asset)
            self._updateAssetStateInternal(asset, _totalBalance)
            self._rewardConfig.updateEmissionPerSecond(asset, distributionPerDay)

    def _updateAssetStateInternal(self, _asset: Address, _totalBalance: int) -> int:
        oldIndex = self._assetIndex[_asset]
        lastUpdateTimestamp = self._lastUpdateTimestamp[_asset]

        currentTime = self.now() // 10 ** 6

        if currentTime == lastUpdateTimestamp:
            return oldIndex
        _emissionPerSecond = self._rewardConfig.getEmissionPerSecond(_asset)

        newIndex = self._getAssetIndex(oldIndex, _emissionPerSecond, lastUpdateTimestamp, _totalBalance)
        if newIndex != oldIndex:
            self._assetIndex[_asset] = newIndex
            self.AssetIndexUpdated(_asset, oldIndex, newIndex)

        self._lastUpdateTimestamp[_asset] = currentTime
        return newIndex

    def _updateUserReserveInternal(self, _user: Address, _asset: Address, _userBalance: int,
                                   _totalBalance: int) -> int:
        userIndex = self._userIndex[_user][_asset]
        accruedRewards = 0

        newIndex = self._updateAssetStateInternal(_asset, _totalBalance)

        if userIndex != newIndex:
            if _userBalance != 0:
                accruedRewards = RewardDistributionManager._getRewards(_userBalance, newIndex, userIndex)
            self._userIndex[_user][_asset] = newIndex
            self.UserIndexUpdated(_user, _asset, userIndex, newIndex)

        return accruedRewards

    def _getAssetIndex(self, _currentIndex: int, _emissionPerSecond: int, _lastUpdateTimestamp: int,
                       _totalBalance: int) -> int:
        currentTime = self.now() // 10 ** 6
        if _emissionPerSecond == 0 or _totalBalance == 0 or _lastUpdateTimestamp == currentTime:
            return _currentIndex
        else:
            timeDelta = currentTime - _lastUpdateTimestamp
            return exaDiv(_emissionPerSecond * timeDelta, _totalBalance) + _currentIndex

    def _getUnclaimedRewards(self, _user: Address, _assetInput: 'UserAssetInput') -> int:
        asset = _assetInput['asset']
        userBalance = _assetInput['userBalance']
        totalBalance = _assetInput['totalBalance']
        _emissionPerSecond = self._rewardConfig.getEmissionPerSecond(asset)
        assetIndex = self._getAssetIndex(self._assetIndex[asset], _emissionPerSecond,
                                         self._lastUpdateTimestamp[asset], totalBalance)
        accruedRewards = RewardDistributionManager._getRewards(userBalance, assetIndex, self._userIndex[_user][asset])
        return accruedRewards

    @staticmethod
    def _getRewards(_userBalance: int, _assetIndex: int, _userIndex: int) -> int:
        return exaMul(_userBalance, _assetIndex - _userIndex)

    @external(readonly=True)
    def tokenDistributionPerDay(self, _day: int) -> int:
        DAYS_PER_YEAR = 365

        if _day < 0:
            return 0
        elif _day < 30:
            return 10 ** 24
        elif _day < DAYS_PER_YEAR:
            return 4 * 10 ** 23
        elif _day < (DAYS_PER_YEAR * 2):
            return 3 * 10 ** 23
        elif _day < (DAYS_PER_YEAR * 3):
            return 2 * 10 ** 23
        elif _day < (DAYS_PER_YEAR * 4):
            return 10 ** 23
        else:
            index = _day // 365 - 4
            return ((103 ** index * 3 * (383 * 10 ** 24)) // DAYS_PER_YEAR) // (100 ** (index + 1))

    @external(readonly=True)
    def getDay(self) -> int:
        return (self.now() - self._timestampAtStart.get()) // DAY_IN_MICROSECONDS

    @external(readonly=True)
    def getStartTimestamp(self) -> int:
        return self._timestampAtStart.get()

    def _getTotalBalance(self, asset) -> int:
        poolId = self._rewardConfig.getPoolID(asset)
        if poolId > 0:
            lp = self.create_interface_score(self._addresses[STAKED_LP], LPInterface)
            return lp.getTotalStaked(poolId)
        else:
            token = self.create_interface_score(asset, TokenInterface)
            return token.getTotalStaked()

    def _getUserAssetDetails(self, asset: Address, user: Address) -> UserAssetInput:
        poolId = self._rewardConfig.getPoolID(asset)
        if poolId > 0:
            lp = self.create_interface_score(self._addresses[STAKED_LP], LPInterface)
            supply = lp.getLPStakedSupply(poolId, user)
        else:
            token = self.create_interface_score(asset, TokenInterface)
            supply = token.getPrincipalSupply(user)
        return {
            'asset': asset,
            'userBalance': supply['principalUserBalance'],
            'totalBalance': supply['principalTotalSupply']
        }
