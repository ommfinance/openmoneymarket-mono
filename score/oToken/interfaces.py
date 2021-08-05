from iconservice import *

class SupplyDetails(TypedDict):
    principalUserBalance: int
    principalTotalSupply: int


class AddressDetails(TypedDict):
    name: str
    address: Address


class LendingPoolCoreInterface(InterfaceScore):
    @interface
    def getNormalizedIncome(self, _reserve: Address) -> int:
        pass

    @interface
    def getReserveLiquidityCumulativeIndex(self, _reserve: Address) -> int:
        pass


class DistributionManager(InterfaceScore):
    @interface
    def handleAction(self, _user: Address, _userBalance: int, _totalSupply: int) -> None:
        pass


class DataProviderInterface(InterfaceScore):
    @interface
    def balanceDecreaseAllowed(self, _underlyingAssetAddress: Address, _user: Address, _amount: int):
        pass


# An interface of tokenFallback.
# Receiving SCORE that has implemented this interface can handle
# the receiving or further routine.
class TokenFallbackInterface(InterfaceScore):
    @interface
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        pass

