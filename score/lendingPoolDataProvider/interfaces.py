from iconservice import *

class SupplyDetails(TypedDict):
    principalUserBalance: int
    principalTotalSupply: int
    decimals: int


class RewardPercentage(TypedDict):
    reserve: Address
    rewardPercentage: int
    lendingPercentage: int
    borrowingPercentage: int


class DistPercentage(TypedDict):
    recipient: str
    distPercentage: int


class AddressDetails(TypedDict):
    name: str
    address: Address


# An interface to fee provider
class FeeProviderInterface(InterfaceScore):
    @interface
    def calculateOriginationFee(self, _user: Address, _amount: int) -> int:
        pass

    @interface
    def getLoanOriginationFeePercentage(self) -> int:
        pass


# An interface to LendingPoolCore
class CoreInterface(InterfaceScore):
    @interface
    def getReserves(self) -> list:
        pass

    @interface
    def getUserBasicReserveData(self, _reserve: Address, _user: Address) -> dict:
        pass

    @interface
    def getReserveConfiguration(self, _reserve: Address) -> dict:
        pass

    @interface
    def getReserveData(self, _reserve: Address) -> dict:
        pass

    @interface
    def getUserReserveData(self, _reserve: Address, _user: Address) -> dict:
        pass

    @interface
    def getCompoundedBorrowBalance(self, _reserve: Address, _user: Address) -> int:
        pass


# An interface to PriceOracle
class OracleInterface(InterfaceScore):
    @interface
    def get_reference_data(self, _base: str, _quote: str) -> int:
        pass


# An interface to oToken
class oTokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def principalBalanceOf(self, _user: Address) -> int:
        pass

    @interface
    def getUserLiquidityCumulativeIndex(self, _user: Address) -> int:
        pass

    @interface
    def getPrincipalSupply(self, _user: Address) -> SupplyDetails:
        pass


# An interface to oToken
class dTokenInterface(InterfaceScore):
    @interface
    def balanceOf(self, _owner: Address) -> int:
        pass

    @interface
    def getUserBorrowCumulativeIndex(self, _user: Address) -> int:
        pass

    @interface
    def principalBalanceOf(self, _user: Address) -> int:
        pass

    @interface
    def getPrincipalSupply(self, _user: Address) -> SupplyDetails:
        pass


# An interface to LendingPool
class LendingPoolInterface(InterfaceScore):
    @interface
    def getBorrowWallets(self, _index: int) -> list:
        pass

    @interface
    def getLoanOriginationFeePercentage(self) -> int:
        pass


# An interface to liquidation manager
class LiquidationInterface(InterfaceScore):
    @interface
    def calculateBadDebt(self, _totalBorrowBalanceUSD: int, _totalFeesUSD: int, _totalCollateralBalanceUSD: int,
                         _ltv: int) -> int:
        pass


class StakingInterface(InterfaceScore):
    @interface
    def getTodayRate(self) -> int:
        pass

    @interface
    def getUserUnstakeInfo(self, _address: Address) -> list:
        pass


class RewardInterface(InterfaceScore):

    @interface
    def getRecipients(self) -> list:
        pass

    @interface
    def getAllDistributionPercentage(self) -> dict:
        pass

    @interface
    def assetDistPercentage(self, asset: Address) -> int:
        pass
