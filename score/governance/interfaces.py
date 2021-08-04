from iconservice import *


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
