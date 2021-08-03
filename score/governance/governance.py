from .utils.checks import *

REWARDS = 'rewards'
LENDING_POOL_CORE = 'lendingPoolCore'
STAKED_LP = 'stakedLP'


class Constant(TypedDict):
    reserve: Address
    optimalUtilizationRate: int
    baseBorrowRate: int
    slopeRate1: int
    slopeRate2: int


class AddressDetails(TypedDict):
    name: str
    address: Address


class ReserveAttributes(TypedDict):
    reserveAddress: Address
    oTokenAddress: Address
    dTokenAddress: Address
    lastUpdateTimestamp: int
    liquidityRate: int
    borrowRate: int
    liquidityCumulativeIndex: int
    borrowCumulativeIndex: int
    baseLTVasCollateral: int
    liquidationThreshold: int
    liquidationBonus: int
    decimals: int
    borrowingEnabled: bool
    usageAsCollateralEnabled: bool
    isFreezed: bool
    isActive: bool


class AssetConfig(TypedDict):
    poolID: int
    asset: Address
    distPercentage: int
    assetName: str
    rewardEntity: str


class RewardInterface(InterfaceScore):

    @interface
    def setStartTimestamp(self, _timestamp: int):
        pass

    @interface
    def configureAssetConfig(self, _assetConfig: AssetConfig) -> None:
        pass

    @interface
    def removeAssetConfig(self, _asset: Address) -> None:
        pass

    @interface
    def getPoolIDByAsset(self, _asset: Address) -> int:
        pass


class StakedLPInterface(InterfaceScore):
    @interface
    def addPool(self, _id: int, _pool: Address) -> None:
        pass

    @interface
    def removePool(self, _id) -> None:
        pass


class CoreInterface(InterfaceScore):
    @interface
    def updateIsFreezed(self, _reserve: Address, _isFreezed: bool):
        pass

    @interface
    def updateIsActive(self, _reserve: Address, _isActive: bool):
        pass

    @interface
    def setReserveConstants(self, _constants: List[Constant]) -> None:
        pass

    @interface
    def addReserveData(self, _reserve: ReserveAttributes):
        pass

    @interface
    def updateBaseLTVasCollateral(self, _reserve: Address, _baseLTVasCollateral: int):
        pass

    @interface
    def updateLiquidationThreshold(self, _reserve: Address, _liquidationThreshold: int):
        pass

    @interface
    def updateLiquidationBonus(self, _reserve: Address, _liquidationBonus: int):
        pass

    @interface
    def updateBorrowingEnabled(self, _reserve: Address, _borrowingEnabled: bool):
        pass

    @interface
    def updateUsageAsCollateralEnabled(self, _reserve: Address, _usageAsCollateralEnabled: bool):
        pass


class Governance(IconScoreBase):
    _CONTRACTS = 'contracts'
    _ADDRESSES = 'addresses'

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._addresses = DictDB(self._ADDRESSES, db, value_type=Address)
        self._contracts = ArrayDB(self._CONTRACTS, db, value_type=str)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "OmmGovernanceManager"

    @origin_owner
    @external
    def setAddresses(self, _addressDetails: List[AddressDetails]) -> None:
        for contracts in _addressDetails:
            if contracts['name'] not in self._contracts:
                self._contracts.put(contracts['name'])
            self._addresses[contracts['name']] = contracts['address']

    @external(readonly=True)
    def getAddresses(self) -> dict:
        return {item: self._addresses[item] for item in self._contracts}

    @only_owner
    @external
    def setStartTimestamp(self, _timestamp: int) -> None:
        rewards = self.create_interface_score(self._addresses[REWARDS], RewardInterface)
        rewards.setStartTimestamp(_timestamp)

    @only_owner
    @external
    def setReserveActiveStatus(self, _reserve: Address, _status: bool):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateIsActive(_reserve, _status)

    @only_owner
    @external
    def setReserveFreezeStatus(self, _reserve: Address, _status: bool):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateIsFreezed(_reserve, _status)

    @only_owner
    @external
    def setReserveConstants(self, _constants: List[Constant]):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.setReserveConstants(_constants)

    @only_owner
    @external
    def initializeReserve(self, _reserve: ReserveAttributes):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.addReserveData(_reserve)

    @only_owner
    @external
    def updateBaseLTVasCollateral(self, _reserve: Address, _baseLtv: int):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateBaseLTVasCollateral(_reserve, _baseLtv)

    @only_owner
    @external
    def updateLiquidationThreshold(self, _reserve: Address, _liquidationThreshold: int):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateLiquidationThreshold(_reserve, _liquidationThreshold)

    @only_owner
    @external
    def updateLiquidationBonus(self, _reserve: Address, _liquidationBonus: int):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateLiquidationBonus(_reserve, _liquidationBonus)

    @only_owner
    @external
    def updateBorrowingEnabled(self, _reserve: Address, _borrowingEnabled: bool):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateBorrowingEnabled(_reserve, _borrowingEnabled)

    @only_owner
    @external
    def updateUsageAsCollateralEnabled(self, _reserve: Address, _usageAsCollateralEnabled: bool):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateUsageAsCollateralEnabled(_reserve, _usageAsCollateralEnabled)

    @only_owner
    @external
    def addPools(self, _assetConfigs: List[AssetConfig]):
        for assetConfig in _assetConfigs:
            self.addPool(assetConfig)

    @only_owner
    @external
    def addPool(self, _assetConfig: AssetConfig):
        _poolID = _assetConfig['poolID']
        if _poolID > 0:
            asset = _assetConfig['asset']
            stakedLP = self.create_interface_score(self._addresses[STAKED_LP], StakedLPInterface)
            stakedLP.addPool(_poolID, asset)

        rewards = self.create_interface_score(self._addresses[REWARDS], RewardInterface)
        rewards.configureAssetConfig(_assetConfig)

    @only_owner
    @external
    def removePool(self, _asset: Address):
        rewards = self.create_interface_score(self._addresses[REWARDS], RewardInterface)
        _poolID = rewards.getPoolIDByAsset(_asset)
        if _poolID > 0:
            stakedLP = self.create_interface_score(self._addresses[STAKED_LP], StakedLPInterface)
            stakedLP.removePool(_poolID)
        rewards.removeAssetConfig(_asset)
