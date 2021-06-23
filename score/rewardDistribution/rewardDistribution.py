from iconservice import *
from .Math import *
from .utils.checks import *

TAG = 'RewardDistributionManager'


class AssetConfig(TypedDict):
    asset: Address
    emissionPerSecond: int
    totalBalance: int


class UserAssetInput(TypedDict):
    asset: Address
    userBalance: int
    totalBalance: int


class RewardDistributionManager(IconScoreBase):
    EMISSION_PER_SECOND = 'emissionPerSecond'
    LAST_UPDATE_TIMESTAMP = 'lastUpdateTimestamp'
    ASSET_INDEX = 'assetIndex'
    USER_INDEX = 'userIndex'
    ASSETS = 'assets'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._emissionPerSecond = DictDB(self.EMISSION_PER_SECOND, db, value_type=int)
        self._lastUpdateTimestamp = DictDB(self.LAST_UPDATE_TIMESTAMP, db, value_type=int)
        self._assetIndex = DictDB(self.ASSET_INDEX, db, value_type=int)
        self._userIndex = DictDB(self.USER_INDEX, db, value_type=int, depth=2)
        self._assets = ArrayDB(self.ASSETS, db, value_type=Address)



    @eventlog(indexed=1)
    def AssetIndexUpdated(self, _asset: Address, _index: int) -> None:
        pass

    @eventlog(indexed=2)
    def UserIndexUpdated(self, _user: Address, _asset: Address, _index: int) -> None:
        pass

    @eventlog(indexed=1)
    def AssetConfigUpdated(self, _asset: Address, _emissionPerSecond: int) -> None:
        pass

    @external(readonly=True)
    def getAssetEmission(self) -> dict:
        return {
            str(asset): self._emissionPerSecond[asset]
            for asset in self._assets
        }

    @external(readonly=True)
    def getAssets(self) -> list:
        return [i for i in self._assets]

    @only_owner
    @external   
    def configureAssetEmission(self, _assetConfig: List[AssetConfig]) -> None:

        for config in _assetConfig:
            asset = config['asset']
            totalBalance = config['totalBalance']
            emissionPerSecond = config['emissionPerSecond']
            self._updateAssetStateInternal(asset, totalBalance)
            self._emissionPerSecond[asset] = emissionPerSecond
            self.AssetConfigUpdated(asset, emissionPerSecond)
            if asset not in self._assets:
                self._assets.put(asset)

    def _updateAssetStateInternal(self, _asset: Address, _totalBalance: int) -> int:
        oldIndex = self._assetIndex[_asset]
        lastUpdateTimestamp = self._lastUpdateTimestamp[_asset]

        if self.now() == lastUpdateTimestamp:
            return oldIndex

        newIndex = self._getAssetIndex(oldIndex, self._emissionPerSecond[_asset], lastUpdateTimestamp, _totalBalance)
        if newIndex != oldIndex:
            self._assetIndex[_asset] = newIndex
            self.AssetIndexUpdated(_asset, newIndex)

        self._lastUpdateTimestamp[_asset] = self.now()
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
            self.UserIndexUpdated(_user, _asset, newIndex)

        return accruedRewards

    def _getAssetIndex(self, _currentIndex: int, _emissionPerSecond: int, _lastUpdateTimestamp: int,
                       _totalBalance: int) -> int:
        if _emissionPerSecond == 0 or _totalBalance == 0 or _lastUpdateTimestamp == self.now():
            return _currentIndex
        else:
            timeDelta = (self.now() - _lastUpdateTimestamp) // 10 ** 6
            return exaDiv(_emissionPerSecond * timeDelta, _totalBalance) + _currentIndex

    def _claimRewards(self, _user: Address, assetInputs: List[UserAssetInput]) -> int:
        accruedRewards = 0
        for asset in assetInputs:
            accruedRewards += self._updateUserReserveInternal(_user, asset['asset'], asset['userBalance'],
                                                              asset['totalBalance'])

        return accruedRewards

    def _getUnclaimedRewards(self, _user: Address, assetInputs: List[UserAssetInput]) -> int:
        accruedRewards = 0
        for assetInput in assetInputs:
            asset = assetInput['asset']
            userBalance = assetInput['userBalance']
            totalBalance = assetInput['totalBalance']
            assetIndex = self._getAssetIndex(self._assetIndex[asset], self._emissionPerSecond[asset],
                                             self._lastUpdateTimestamp[asset], totalBalance)

            accruedRewards += RewardDistributionManager._getRewards(userBalance, assetIndex, self._userIndex[_user][asset])

        return accruedRewards

    @staticmethod
    def _getRewards(_userBalance: int, _assetIndex: int, _userIndex: int) -> int:
        return exaMul(_userBalance, _assetIndex - _userIndex)
