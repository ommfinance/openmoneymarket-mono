from .Math import *
from .utils.checks import *

TAG = 'RewardDistributionManager'

DAY_IN_MICROSECONDS = 86400 * 10 ** 6


class AssetConfig(TypedDict):
    asset: Address
    distPercentage: int

class LPConfig(TypedDict):
    id: int
    distPercentage: int


class UserAssetInput(TypedDict):
    asset: Address
    userBalance: int
    totalBalance: int


class TokenInterface(InterfaceScore):
    @interface
    def totalSupply(self) -> int:
        pass

    @interface
    def total_staked_balance(self) -> int:
        pass

class LPStakingInterface(InterfaceScore):

    @interface
    def getTotalStaked(self, _id: int) -> int:
        pass

    @interface
    def getPoolById(self, _id: int ) -> Address:
        pass


class RewardDistributionManager(IconScoreBase):
    EMISSION_PER_SECOND = 'emissionPerSecond'
    LAST_UPDATE_TIMESTAMP = 'lastUpdateTimestamp'
    ASSET_INDEX = 'assetIndex'
    USER_INDEX = 'userIndex'
    ASSETS = 'assets'
    DIST_PERCENTAGE = 'distPercentage'
    RESERVE_ASSETS = 'reserveAssets'
    LP_IDS = 'lpIds'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._emissionPerSecond = DictDB(self.EMISSION_PER_SECOND, db, value_type=int)
        self._lastUpdateTimestamp = DictDB(self.LAST_UPDATE_TIMESTAMP, db, value_type=int)
        self._assetIndex = DictDB(self.ASSET_INDEX, db, value_type=int)
        self._distPercentage = DictDB(self.DIST_PERCENTAGE, db, value_type=int)
        self._userIndex = DictDB(self.USER_INDEX, db, value_type=int, depth=2)
        self._assets = ArrayDB(self.ASSETS, db, value_type=Address)
        self._reserveAssets = ArrayDB(self.RESERVE_ASSETS, db, value_type=Address)
        self._lpIds = ArrayDB(self.LP_IDS, db, value_type=int)
        self._timestampAtStart = VarDB('timestampAtStart', db, value_type=int)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

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
        return [asset for asset in self._assets]


    def _configureEmissionPerSecond(self, asset: Address, distPercentage: int, totalBalance: int):
        self._distPercentage[asset] = distPercentage
        emissionPerSecond = self._getEmissionPerSecond(distPercentage)
        self._updateAssetStateInternal(asset, totalBalance)
        self._emissionPerSecond[asset] = emissionPerSecond
        self.AssetConfigUpdated(asset, emissionPerSecond)
        if asset not in self._assets:
            self._assets.put(asset)

    @only_owner
    @external
    def configureAssetEmission(self, _assetConfig: List[AssetConfig]) -> None:
        for config in _assetConfig:
            asset = config['asset']
            distPercentage = config['distPercentage']
            token = self.create_interface_score(asset, TokenInterface)
            totalBalance = token.totalSupply()
            self._configureEmissionPerSecond(asset, distPercentage, totalBalance)
            if reserveAsset not in self._reserveAssets:
                self._reserveAssets.put(reserveAsset)


    @only_owner
    @external
    def configureLPEmission(self, _lpConfig: List[LPConfig]) -> None:
        for config in _lpConfig:
            id = config['id']
            distPercentage = config['distPercentage']
            lp = self.create_interface_score(self._addresses['stakedLp'], LpInterface)
            asset = lp.getPoolById(id)
            totalStakeBalance = lp.getTotalStaked(id)
            self._configureEmissionPerSecond(asset, distPercentage, totalStakeBalance)
            if lpId not in self._lpIds:
                self._lpIds.put(lpId)

    @only_owner
    @external
    def configureOmmEmission(self, _distPercentage: int) -> None:
        asset = self._addresses['ommToken']
        token = self.create_interface_score(asset, TokenInterface)
        totalStakedBalance = token.total_staked_balance()
        self._configureEmissionPerSecond(asset, _distPercentage, totalStakedBalance)
    

    @only_owner
    def updateEmissionPerSecond(self) -> None:
        for asset in self._reserveAssets:
            distPercentage = self._distPercentage[asset]
            token = self.create_interface_score(asset, TokenInterface)
            totalBalance = token.totalSupply()
            self._configureEmissionPerSecond(asset, distPercentage, totalBalance)

        for lpId in self._lpId:
            lp = self.create_interface_score(self._addresses['stakedLp'], LpInterface)
            asset = lp.getPoolById(id)
            totalStakeBalance = lp.getTotalStaked(id)
            distPercentage = self._distPercentage[asset]
            self._configureEmissionPerSecond(asset, distPercentage, totalStakeBalance)
        
        asset = self._addresses['ommToken']
        token = self.create_interface_score(asset, TokenInterface)
        totalStakedBalance = token.total_staked_balance()
        distPercentage = self._distPercentage[asset]
        self._configureEmissionPerSecond(asset, _distPercentage, totalStakedBalance)


    def _updateAssetStateInternal(self, _asset: Address, _totalBalance: int) -> int:
        oldIndex = self._assetIndex[_asset]
        lastUpdateTimestamp = self._lastUpdateTimestamp[_asset]

        currentTime = self.now() // 10 ** 6

        if currentTime == lastUpdateTimestamp:
            return oldIndex

        newIndex = self._getAssetIndex(oldIndex, self._emissionPerSecond[_asset], lastUpdateTimestamp, _totalBalance)
        if newIndex != oldIndex:
            self._assetIndex[_asset] = newIndex
            self.AssetIndexUpdated(_asset, newIndex)

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
            self.UserIndexUpdated(_user, _asset, newIndex)

        return accruedRewards

    def _getAssetIndex(self, _currentIndex: int, _emissionPerSecond: int, _lastUpdateTimestamp: int,
                       _totalBalance: int) -> int:
        currentTime = self.now() // 10 ** 6
        if _emissionPerSecond == 0 or _totalBalance == 0 or _lastUpdateTimestamp == currentTime:
            return _currentIndex
        else:
            timeDelta = currentTime - _lastUpdateTimestamp
            return exaDiv(_emissionPerSecond * timeDelta, _totalBalance) + _currentIndex

    def _claimRewards(self, _user: Address, assetInputs: List[UserAssetInput]) -> int:
        accruedRewards = 0
        for asset in assetInputs:
            accruedRewards += self._updateUserReserveInternal(_user, asset['asset'], asset['userBalance'],
                                                              asset['totalBalance'])

        return accruedRewards

    def _getUnclaimedRewards(self, _user: Address, _assetInput: 'UserAssetInput') -> int:
        asset = _assetInput['asset']
        userBalance = _assetInput['userBalance']
        totalBalance = _assetInput['totalBalance']
        assetIndex = self._getAssetIndex(self._assetIndex[asset], self._emissionPerSecond[asset],
                                         self._lastUpdateTimestamp[asset], totalBalance)
        accruedRewards = RewardDistributionManager._getRewards(userBalance, assetIndex, self._userIndex[_user][asset])
        return accruedRewards

    @staticmethod
    def _getRewards(_userBalance: int, _assetIndex: int, _userIndex: int) -> int:
        return exaMul(_userBalance, _assetIndex - _userIndex)

    def _getEmissionPerSecond(self, distributionPercent):
        distributionPerDay = self.tokenDistributionPerDay(self.getDay());
        return exaDiv(distributionPerDay // 86400, distributionPercent)

    @external(readonly=True)
    def tokenDistributionPerDay(self, _day: int) -> int:
        DAYS_PER_YEAR = 365

        if _day < 30:
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

    @only_governance
    @external
    def setStartTimestamp(self, _timestamp: int):
        self._timestampAtStart.set(_timestamp)

    @external(readonly=True)
    def getStartTimestamp(self) -> int:
        return self._timestampAtStart.get()
