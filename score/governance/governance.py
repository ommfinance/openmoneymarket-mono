from .utils.checks import *
from .addresses import *
from .interfaces import *


class Governance(Addresses):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self, _addressProvider: Address) -> None:
        super().on_install(_addressProvider)

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def name(self) -> str:
        return "OmmGovernanceManager"

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
    def updateBorrowThreshold(self, _reserve: Address, _borrowThreshold: int):
        core = self.create_interface_score(self._addresses[LENDING_POOL_CORE], CoreInterface)
        core.updateBorrowThreshold(_reserve, _borrowThreshold)

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
